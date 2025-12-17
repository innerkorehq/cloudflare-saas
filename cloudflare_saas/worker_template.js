/**
 * Cloudflare Worker for multi-tenant site routing
 * 
 * This worker:
 * - Resolves tenant from Host header
 * - Serves static files from R2 with tenant namespace
 * - Sets appropriate cache headers
 * - Handles SPA fallback to index.html
 */

const ORIGIN_CACHE_TTL = 60 * 60 * 24 * 7; // 7 days
const INDEX_CACHE_TTL = 60; // 1 minute

// Simple LRU cache for host->tenant mapping
class LRUCache {
  constructor(maxSize = 1000) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key) {
    if (!this.cache.has(key)) return undefined;
    const value = this.cache.get(key);
    this.cache.delete(key);
    this.cache.set(key, value);
    return value;
  }

  set(key, value) {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, value);
  }
}

const hostCache = new LRUCache(1000);

async function resolveTenantFromHost(host, env) {
  // Check cache
  const cached = hostCache.get(host);
  if (cached) return cached;

  // Fast path: subdomain
  const platformDomain = env.PLATFORM_DOMAIN || 'yourplatform.com';
  if (host.endsWith(`.${platformDomain}`)) {
    const tenantId = host.slice(0, host.length - platformDomain.length - 1);
    hostCache.set(host, tenantId);
    return tenantId;
  }

  // Slow path: query platform API for custom domains
  try {
    const apiUrl = `https://api.${platformDomain}/internal/resolve?host=${encodeURIComponent(host)}`;
    const resp = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${env.INTERNAL_API_KEY}`,
      },
    });

    if (resp.ok) {
      const data = await resp.json();
      if (data.tenant_id) {
        hostCache.set(host, data.tenant_id);
        return data.tenant_id;
      }
    }
  } catch (error) {
    console.error('Failed to resolve custom domain:', error);
  }

  return null;
}

function guessContentType(path) {
  const ext = path.split('.').pop().toLowerCase();
  const types = {
    'html': 'text/html; charset=utf-8',
    'css': 'text/css',
    'js': 'application/javascript',
    'json': 'application/json',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'webp': 'image/webp',
    'ico': 'image/x-icon',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
    'eot': 'application/vnd.ms-fontobject',
  };
  return types[ext] || 'application/octet-stream';
}

function computeCacheControl(key) {
  // HTML files: short cache for updates
  if (key.endsWith('.html')) {
    return 'public, max-age=0, s-maxage=60, must-revalidate';
  }
  
  // Static assets: long cache with immutable
  if (key.match(/\.(css|js|png|jpg|jpeg|gif|svg|webp|ico|woff|woff2|ttf|eot)$/i)) {
    return `public, max-age=${ORIGIN_CACHE_TTL}, immutable, s-maxage=${ORIGIN_CACHE_TTL}`;
  }
  
  // Default
  return 'public, max-age=3600, s-maxage=3600';
}

async function handleRequest(request, env) {
  const url = new URL(request.url);
  const host = request.headers.get('host');

  // Health check
  if (url.pathname === '/_health') {
    return new Response('OK', { status: 200 });
  }

  // Resolve tenant
  const tenantId = await resolveTenantFromHost(host, env);
  if (!tenantId) {
    return new Response('Site not found', { 
      status: 404,
      headers: { 'content-type': 'text/plain' },
    });
  }

  // Map path to R2 key
  let key = url.pathname;
  if (key === '/' || key === '') {
    key = '/index.html';
  }

  // Remove leading slash for R2
  if (key.startsWith('/')) {
    key = key.slice(1);
  }

  const objectKey = `${tenantId}/${key}`;

  // Try to get object from R2
  try {
    const obj = await env.MY_BUCKET.get(objectKey);
    
    if (obj) {
      const headers = new Headers();
      
      // Content type
      const contentType = obj.httpMetadata?.contentType || guessContentType(objectKey);
      headers.set('content-type', contentType);
      
      // Cache control
      headers.set('cache-control', computeCacheControl(objectKey));
      
      // CORS (optional, adjust as needed)
      headers.set('access-control-allow-origin', '*');
      
      // Security headers
      headers.set('x-content-type-options', 'nosniff');
      headers.set('x-frame-options', 'SAMEORIGIN');
      
      return new Response(obj.body, { 
        status: 200, 
        headers,
      });
    }

    // Fallback for SPA: try index.html
    if (!key.includes('.')) {
      const indexKey = `${tenantId}/index.html`;
      const idx = await env.MY_BUCKET.get(indexKey);
      
      if (idx) {
        const headers = new Headers();
        headers.set('content-type', 'text/html; charset=utf-8');
        headers.set('cache-control', `public, max-age=0, s-maxage=${INDEX_CACHE_TTL}`);
        headers.set('x-content-type-options', 'nosniff');
        headers.set('x-frame-options', 'SAMEORIGIN');
        
        return new Response(idx.body, { 
          status: 200, 
          headers,
        });
      }
    }

    return new Response('Not Found', { 
      status: 404,
      headers: { 'content-type': 'text/plain' },
    });

  } catch (error) {
    console.error('R2 error:', error);
    return new Response('Internal Server Error', { 
      status: 500,
      headers: { 'content-type': 'text/plain' },
    });
  }
}

export default {
  async fetch(request, env, ctx) {
    try {
      return await handleRequest(request, env);
    } catch (error) {
      console.error('Worker error:', error);
      return new Response('Internal Server Error', { 
        status: 500,
        headers: { 'content-type': 'text/plain' },
      });
    }
  }
};
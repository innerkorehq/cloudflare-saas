/**
 * Cloudflare Worker for multi-tenant site routing with D1 database
 * 
 * This worker:
 * - Resolves tenant from Host header
 * - Serves static files from R2 with tenant namespace
 * - Sets appropriate cache headers
 * - Handles Next.js App Router static export routing
 * - Queries D1 database for custom domain resolution
 * 
 * Next.js Static Export Handling:
 * With `output: 'export'` and `trailingSlash: false` (default), Next.js generates:
 * - / → index.html
 * - /about → about.html
 * - /blog/post → blog/post.html
 * 
 * The worker tries paths in this order (mimicking nginx try_files):
 * 1. Exact path (for assets like .js, .css, images)
 * 2. Path + .html (for Next.js pages)
 * 3. Path + /index.html (for directory indexes)
 * 4. Fallback to /index.html (for client-side routing)
 */

const ORIGIN_CACHE_TTL = 60 * 60 * 24 * 7; // 7 days
async function resolveTenantFromHost(host, env) {
  // Fast path: subdomain
  const platformDomain = env.PLATFORM_DOMAIN || 'yourplatform.com';
  console.log(`[resolve] host=${host} platformDomain=${platformDomain}`);

  if (host.endsWith(`.${platformDomain}`)) {
    const tenantId = host.slice(0, host.length - platformDomain.length - 1);
    console.log(`[resolve] subdomain match → tenantId=${tenantId}`);
    return tenantId;
  }

  // Query D1 database for custom domains
  if (!env.DB) {
    console.error('[resolve] env.DB is not bound — check wrangler.toml [[d1_databases]] binding');
    return null;
  }

  try {
    const defaultZone = env.DEFAULT_ZONE || 'default';
    console.log(`[resolve] querying D1 for host=${host} zone=${defaultZone}`);
    const stmt = env.DB.prepare(
      'SELECT tenant_id FROM domains WHERE name = ? AND zone = ?'
    ).bind(host, defaultZone);
    const result = await stmt.first();
    console.log(`[resolve] D1 result=${JSON.stringify(result)}`);
    if (result && result.tenant_id) {
      return result.tenant_id;
    }
  } catch (error) {
    console.error('[resolve] D1 query failed:', error);
  }

  console.warn(`[resolve] no tenant found for host=${host}`);
  return null;
}

function guessContentType(path) {
  const ext = path.split('.').pop().toLowerCase();
  const types = {
    'html': 'text/html; charset=utf-8',
    'css': 'text/css; charset=utf-8',
    'js': 'text/javascript; charset=utf-8',
    'mjs': 'text/javascript; charset=utf-8',
    'json': 'application/json; charset=utf-8',
    'map': 'application/json; charset=utf-8',
    'xml': 'application/xml; charset=utf-8',
    'txt': 'text/plain; charset=utf-8',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml; charset=utf-8',
    'webp': 'image/webp',
    'avif': 'image/avif',
    'ico': 'image/x-icon',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
    'otf': 'font/otf',
    'eot': 'application/vnd.ms-fontobject',
    'pdf': 'application/pdf',
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mp3': 'audio/mpeg',
    'ogg': 'audio/ogg',
  };
  return types[ext] || 'application/octet-stream';
}

function computeCacheControl(key) {
  if (key.endsWith('.html')) {
    return 'public, max-age=0, s-maxage=60, must-revalidate';
  }
  return `public, max-age=${ORIGIN_CACHE_TTL}`;
}

function buildR2Response(obj, objectKey) {
  const storedType = obj.httpMetadata?.contentType;
  const guessedType = guessContentType(objectKey);
  let contentType;
  if (storedType) {
    const storedMain = storedType.split(';')[0].trim().toLowerCase();
    const guessedMain = guessedType.split(';')[0].trim().toLowerCase();
    if (storedMain === guessedMain) {
      contentType = storedType;
    } else {
      console.warn(`[r2] contentType mismatch for ${objectKey}: stored=${storedType} guessed=${guessedType} — using guessed`);
      contentType = guessedType;
    }
  } else {
    contentType = guessedType;
  }
  const headers = new Headers();
  headers.set('content-type', contentType);
  headers.set('cache-control', computeCacheControl(objectKey));
  headers.set('access-control-allow-origin', '*');
  headers.set('x-content-type-options', 'nosniff');
  headers.set('x-frame-options', 'SAMEORIGIN');
  return new Response(obj.body, { status: 200, headers });
}

async function handleRequest(request, env) {
  const url = new URL(request.url);
  const host = request.headers.get('host');

  // Health check
  if (url.pathname === '/_health') {
    return new Response('OK', { status: 200, headers: { 'content-type': 'text/plain; charset=utf-8' } });
  }

  // Resolve tenant
  const tenantId = await resolveTenantFromHost(host, env);
  if (!tenantId) {
    return new Response(`Site not found: ${host}`, { 
      status: 404,
      headers: { 'content-type': 'text/plain; charset=utf-8' },
    });
  }

  // Map path to R2 key
  let pathname = url.pathname;
  
  // Normalize path
  if (pathname === '/' || pathname === '') {
    pathname = '/index.html';
  }

  // Remove leading slash for R2
  let key = pathname.startsWith('/') ? pathname.slice(1) : pathname;

  const STATIC_ASSET_RE = /\.(css|js|mjs|json|map|png|jpg|jpeg|gif|svg|webp|avif|ico|woff|woff2|ttf|otf|eot|pdf|mp4|webm|mp3|ogg|txt|xml)$/i;
  const isStaticAsset = STATIC_ASSET_RE.test(key);

  // Try to get object from R2
  try {
    // Static assets: serve exact key only — no variant guessing, no SPA fallback
    if (isStaticAsset || key.endsWith('.html')) {
      const objectKey = `${tenantId}/${key}`;
      const obj = await env.MY_BUCKET.get(objectKey);
      if (obj) {
        return buildR2Response(obj, objectKey);
      }
      console.warn(`[r2] asset not found: ${objectKey}`);
      return new Response(`Not Found: ${key}`, {
        status: 404,
        headers: { 'content-type': 'text/plain; charset=utf-8' },
      });
    }

    // HTML routes: try key, key/index.html, key.html, then SPA fallback
    const keysToTry = [];
    if (key.endsWith('/')) {
      keysToTry.push(`${key}index.html`);
      keysToTry.push(key.slice(0, -1) + '.html');
    } else {
      keysToTry.push(key);
      keysToTry.push(`${key}/index.html`);
      keysToTry.push(`${key}.html`);
    }

    for (const tryKey of keysToTry) {
      const objectKey = `${tenantId}/${tryKey}`;
      const obj = await env.MY_BUCKET.get(objectKey);
      if (obj) {
        return buildR2Response(obj, objectKey);
      }
    }

    // Final fallback: serve root index.html for SPA client-side routing (HTML pages only)
    const indexKey = `${tenantId}/index.html`;
    const idx = await env.MY_BUCKET.get(indexKey);
    
    if (idx) {
      return buildR2Response(idx, indexKey);
    }

    return new Response('Not Found', { 
      status: 404,
      headers: { 'content-type': 'text/plain; charset=utf-8' },
    });

  } catch (error) {
    console.error('R2 error:', error);
    return new Response('Internal Server Error', { 
      status: 500,
      headers: { 'content-type': 'text/plain; charset=utf-8' },
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
        headers: { 'content-type': 'text/plain; charset=utf-8' },
      });
    }
  }
};

"""PostgreSQL storage adapter using asyncpg."""

from typing import Optional, List
import asyncpg
from asyncpg.pool import Pool

from .models import Tenant, CustomDomain, DomainStatus, VerificationMethod
from .storage_adapter import StorageAdapter
from .exceptions import CloudflareSaaSException


class PostgresStorageAdapter(StorageAdapter):
    """PostgreSQL storage implementation."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool: Optional[Pool] = None
    
    async def initialize(self) -> None:
        """Initialize connection pool and create tables."""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20,
        )
        
        await self._create_tables()
    
    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        async with self.pool.acquire() as conn:
            # Tenants table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL UNIQUE,
                    subdomain VARCHAR(255) NOT NULL UNIQUE,
                    owner_id VARCHAR(255),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            # Custom domains table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_domains (
                    domain VARCHAR(255) PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL,
                    verification_method VARCHAR(50) NOT NULL,
                    verification_token VARCHAR(255),
                    cname_target VARCHAR(255),
                    cloudflare_hostname_id VARCHAR(255),
                    ssl_status VARCHAR(50),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    verified_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_domains_tenant_id 
                ON custom_domains(tenant_id)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_domains_status 
                ON custom_domains(status)
            """)
    
    async def save_tenant(self, tenant: Tenant) -> None:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO tenants (tenant_id, name, slug, subdomain, owner_id, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    metadata = EXCLUDED.metadata
            """, tenant.tenant_id, tenant.name, tenant.slug, tenant.subdomain,
                tenant.owner_id, tenant.created_at, tenant.metadata)
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM tenants WHERE tenant_id = $1
            """, tenant_id)
            
            if row:
                return Tenant(**dict(row))
            return None
    
    async def delete_tenant(self, tenant_id: str) -> None:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM tenants WHERE tenant_id = $1
            """, tenant_id)
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM tenants 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            
            return [Tenant(**dict(row)) for row in rows]
    
    async def save_domain(self, domain: CustomDomain) -> None:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO custom_domains (
                    domain, tenant_id, status, verification_method,
                    verification_token, cname_target, cloudflare_hostname_id,
                    ssl_status, created_at, verified_at, error_message
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (domain) DO UPDATE SET
                    status = EXCLUDED.status,
                    cloudflare_hostname_id = EXCLUDED.cloudflare_hostname_id,
                    ssl_status = EXCLUDED.ssl_status,
                    verified_at = EXCLUDED.verified_at,
                    error_message = EXCLUDED.error_message
            """, domain.domain, domain.tenant_id, domain.status.value,
                domain.verification_method.value, domain.verification_token,
                domain.cname_target, domain.cloudflare_hostname_id,
                domain.ssl_status, domain.created_at, domain.verified_at,
                domain.error_message)
    
    async def get_domain(self, domain: str) -> Optional[CustomDomain]:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM custom_domains WHERE domain = $1
            """, domain)
            
            if row:
                data = dict(row)
                data["status"] = DomainStatus(data["status"])
                data["verification_method"] = VerificationMethod(data["verification_method"])
                return CustomDomain(**data)
            return None
    
    async def delete_domain(self, domain: str) -> None:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM custom_domains WHERE domain = $1
            """, domain)
    
    async def list_tenant_domains(self, tenant_id: str) -> List[CustomDomain]:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM custom_domains 
                WHERE tenant_id = $1 
                ORDER BY created_at DESC
            """, tenant_id)
            
            domains = []
            for row in rows:
                data = dict(row)
                data["status"] = DomainStatus(data["status"])
                data["verification_method"] = VerificationMethod(data["verification_method"])
                domains.append(CustomDomain(**data))
            
            return domains
    
    async def get_domain_by_tenant(self, domain: str) -> Optional[str]:
        if not self.pool:
            raise CloudflareSaaSException("Storage not initialized")
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT tenant_id FROM custom_domains 
                WHERE domain = $1 AND status = 'active'
            """, domain)
            
            if row:
                return row["tenant_id"]
            return None
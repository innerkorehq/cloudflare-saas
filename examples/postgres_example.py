"""Example using PostgreSQL storage adapter."""

import asyncio
import os
from cloudflare_saas import (
    CloudflareSaaSPlatform,
    Config,
    PostgresStorageAdapter,
)


async def main():
    """Run example with PostgreSQL storage."""
    # Load config
    config = Config.from_env()
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set: export DATABASE_URL=postgresql://user:pass@host:5432/dbname")
        return
    
    print("Initializing PostgreSQL storage...")
    storage = PostgresStorageAdapter(database_url)
    await storage.initialize()
    
    try:
        print("Creating platform with PostgreSQL storage...")
        platform = CloudflareSaaSPlatform(config, storage)
        
        # Create tenants
        print("\nCreating tenants...")
        tenant1 = await platform.create_tenant("Company A", "company-a", "owner-1")
        tenant2 = await platform.create_tenant("Company B", "company-b", "owner-2")
        
        print(f"✓ Created {tenant1.name}: {tenant1.subdomain}")
        print(f"✓ Created {tenant2.name}: {tenant2.subdomain}")
        
        # List all tenants
        print("\nListing all tenants...")
        tenants = await platform.list_tenants()
        print(f"Total tenants: {len(tenants)}")
        for t in tenants:
            print(f"  - {t.name} ({t.tenant_id})")
        
        # Add custom domain
        print("\nAdding custom domain...")
        instructions = await platform.add_custom_domain(
            tenant1.tenant_id,
            "app.companya.com",
        )
        print(f"✓ Domain added: {instructions.domain}")
        print(f"  CNAME target: {instructions.cname_target}")
        
        # List tenant domains
        domains = await platform.list_tenant_domains(tenant1.tenant_id)
        print(f"\nTenant {tenant1.name} has {len(domains)} domain(s)")
        
        # Resolve tenant from hostname
        print("\nTesting hostname resolution...")
        resolved = await platform.resolve_tenant_from_host(tenant1.subdomain)
        print(f"Resolved {tenant1.subdomain} -> {resolved}")
        
        print("\n✓ PostgreSQL storage example completed successfully!")
        
    finally:
        # Clean up
        print("\nClosing database connection...")
        await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
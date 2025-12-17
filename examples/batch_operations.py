"""Batch operations example for managing multiple tenants."""

import asyncio
from pathlib import Path
from typing import List, Dict
from cloudflare_saas import CloudflareSaaSPlatform, Config


class BatchOperations:
    """Helper class for batch tenant operations."""
    
    def __init__(self, platform: CloudflareSaaSPlatform):
        self.platform = platform
    
    async def create_tenants_batch(
        self,
        tenants_data: List[Dict],
    ) -> List[Dict]:
        """Create multiple tenants concurrently."""
        async def create_tenant(data):
            try:
                tenant = await self.platform.create_tenant(
                    name=data["name"],
                    slug=data["slug"],
                    owner_id=data.get("owner_id"),
                    metadata=data.get("metadata"),
                )
                return {
                    "success": True,
                    "tenant": tenant.dict(),
                }
            except Exception as e:
                return {
                    "success": False,
                    "slug": data["slug"],
                    "error": str(e),
                }
        
        tasks = [create_tenant(data) for data in tenants_data]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        successful = sum(1 for r in results if r["success"])
        print(f"Created {successful}/{len(results)} tenants")
        
        return results
    
    async def deploy_sites_batch(
        self,
        deployments: List[Dict],
    ) -> List[Dict]:
        """Deploy multiple sites concurrently."""
        async def deploy_site(deployment):
            try:
                result = await self.platform.deploy_tenant_site(
                    tenant_id=deployment["tenant_id"],
                    local_path=deployment["local_path"],
                    base_prefix=deployment.get("base_prefix", ""),
                )
                return {
                    "success": result.success,
                    "tenant_id": deployment["tenant_id"],
                    "result": result.dict(),
                }
            except Exception as e:
                return {
                    "success": False,
                    "tenant_id": deployment["tenant_id"],
                    "error": str(e),
                }
        
        tasks = [deploy_site(d) for d in deployments]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        successful = sum(1 for r in results if r["success"])
        print(f"Deployed {successful}/{len(results)} sites")
        
        return results
    
    async def verify_domains_batch(
        self,
        domains: List[str],
        max_wait_seconds: int = 300,
    ) -> Dict[str, str]:
        """Check verification status for multiple domains."""
        async def check_domain(domain):
            try:
                status = await self.platform.get_domain_status(domain)
                return (domain, status.status.value)
            except Exception as e:
                return (domain, f"error: {e}")
        
        tasks = [check_domain(d) for d in domains]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        return dict(results)


async def main():
    """Run batch operations example."""
    config = Config.from_env()
    platform = CloudflareSaaSPlatform(config)
    batch = BatchOperations(platform)
    
    # Example: Create multiple tenants
    print("Creating tenants in batch...")
    tenants_to_create = [
        {"name": "Tenant A", "slug": "tenant-a", "owner_id": "owner-1"},
        {"name": "Tenant B", "slug": "tenant-b", "owner_id": "owner-2"},
        {"name": "Tenant C", "slug": "tenant-c", "owner_id": "owner-3"},
    ]
    
    tenant_results = await batch.create_tenants_batch(tenants_to_create)
    
    for result in tenant_results:
        if result["success"]:
            print(f"  ✓ {result['tenant']['name']}: {result['tenant']['subdomain']}")
        else:
            print(f"  ✗ {result['slug']}: {result['error']}")
    
    # Example: Deploy sites in batch
    print("\nDeploying sites in batch...")
    site_path = Path("./sample-site")
    
    if site_path.exists():
        deployments = [
            {
                "tenant_id": result["tenant"]["tenant_id"],
                "local_path": str(site_path),
            }
            for result in tenant_results if result["success"]
        ]
        
        deploy_results = await batch.deploy_sites_batch(deployments)
        
        for result in deploy_results:
            if result["success"]:
                r = result["result"]
                print(f"  ✓ {result['tenant_id']}: {r['files_uploaded']} files")
            else:
                print(f"  ✗ {result['tenant_id']}: {result['error']}")
    else:
        print(f"  Sample site not found at {site_path}")
    
    print("\n✓ Batch operations completed")


if __name__ == "__main__":
    asyncio.run(main())
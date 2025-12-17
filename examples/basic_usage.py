"""Basic usage example for Cloudflare SaaS Platform."""

import asyncio
from pathlib import Path
from cloudflare_saas import CloudflareSaaSPlatform, Config


async def main():
    # Load config from environment
    config = Config.from_env()
    
    # Or create manually
    # config = Config(
    #     cloudflare_api_token="your-token",
    #     cloudflare_account_id="your-account",
    #     cloudflare_zone_id="your-zone",
    #     r2_access_key_id="your-r2-key",
    #     r2_secret_access_key="your-r2-secret",
    #     r2_bucket_name="yourplatform-sites",
    #     platform_domain="yourplatform.com",
    # )
    
    platform = CloudflareSaaSPlatform(config)
    
    # Create a tenant
    print("Creating tenant...")
    tenant = await platform.create_tenant(
        name="Acme Corporation",
        slug="acme-123",
        owner_id="user-456",
    )
    print(f"✓ Tenant created: {tenant.tenant_id}")
    print(f"  Subdomain: {tenant.subdomain}")
    
    # Deploy site
    print("\nDeploying site...")
    site_path = Path("./sample-site")  # Directory with index.html, etc.
    
    if site_path.exists():
        deployment = await platform.deploy_tenant_site(
            tenant.tenant_id,
            str(site_path),
        )
        
        if deployment.success:
            print(f"✓ Deployed {deployment.files_uploaded} files")
            print(f"  Total size: {deployment.total_size_bytes / 1024:.2f} KB")
            print(f"  Time: {deployment.deployment_time_seconds:.2f}s")
        else:
            print(f"✗ Deployment failed: {deployment.error_message}")
    else:
        print(f"  Site directory not found: {site_path}")
    
    # Add custom domain
    print("\nAdding custom domain...")
    instructions = await platform.add_custom_domain(
        tenant.tenant_id,
        "www.acme.com",
    )
    print(f"✓ Domain verification started")
    print(f"  CNAME target: {instructions.cname_target}")
    print(instructions.instructions)
    
    # Check domain status (after some time)
    print("\nWaiting for verification...")
    await asyncio.sleep(5)
    
    domain_status = await platform.get_domain_status("www.acme.com")
    print(f"  Status: {domain_status.status.value}")
    
    # List tenant domains
    domains = await platform.list_tenant_domains(tenant.tenant_id)
    print(f"\nTenant has {len(domains)} domain(s):")
    for d in domains:
        print(f"  - {d.domain}: {d.status.value}")
    
    # Get deployment status
    status = await platform.get_deployment_status(tenant.tenant_id)
    print(f"\nDeployment status:")
    print(f"  Objects: {status['object_count']}")
    print(f"  Size: {status['total_size_bytes'] / 1024:.2f} KB")
    
    print("\n✓ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
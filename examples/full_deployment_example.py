#!/usr/bin/env python3
"""
Full deployment example for Cloudflare SaaS platform.

This example demonstrates a complete workflow:
1. Upload folder to tenant-specific R2 storage
2. Deploy worker script if not present
3. Configure custom domain for tenant
4. Verify domain configuration

Usage:
    python full_deployment_example.py <folder_path> <tenant_slug> <domain_name>

Example:
    python full_deployment_example.py ./my-website mytenant mytenant.com
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from cloudflare_saas import (
    CloudflareSaaSPlatform,
    Config,
    configure_logging,
    LogLevel,
    LogFormat,
    InMemoryStorageAdapter,
)


async def deploy_tenant_site(
    platform: CloudflareSaaSPlatform,
    folder_path: str,
    tenant_slug: str,
    domain_name: str,
    config: Config,
) -> None:
    """Complete deployment workflow for a tenant site."""

    print(f"🚀 Starting deployment for tenant: {tenant_slug}")
    print(f"📁 Source folder: {folder_path}")
    print(f"🌐 Domain: {domain_name}")
    print()

    # 1. Create or get tenant
    print("1️⃣ Creating/getting tenant...")
    try:
        tenant = await platform.create_tenant(
            name=f"Tenant {tenant_slug.title()}",
            slug=tenant_slug,
            owner_id="example-owner",
        )
        print(f"✅ Tenant created: {tenant.tenant_id}")
        print(f"   Subdomain: {tenant.subdomain}")
    except Exception as e:
        print(f"⚠️  Tenant might already exist, trying to get: {e}")
        tenant = await platform.get_tenant(f"tenant-{tenant_slug}")
        print(f"✅ Tenant found: {tenant.tenant_id}")

    print()

    # 2. Check infrastructure and deploy site to R2
    print("2️⃣ Checking infrastructure and deploying site to R2 storage...")

    # First check if we can access R2
    try:
        # Try a simple R2 operation to check if bucket exists
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        s3_client = boto3.client(
            's3',
            endpoint_url=config.r2_endpoint,
            aws_access_key_id=config.r2_access_key_id,
            aws_secret_access_key=config.r2_secret_access_key,
            region_name='auto',  # R2 uses 'auto' as region
        )

        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=config.r2_bucket_name)
            bucket_exists = True
            print("✅ R2 bucket exists and is accessible")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                bucket_exists = False
                print("❌ R2 bucket does not exist")
            elif e.response['Error']['Code'] == '403':
                bucket_exists = False
                print("❌ R2 bucket access denied (check credentials)")
            else:
                bucket_exists = False
                print(f"❌ R2 bucket check failed: {e}")

    except NoCredentialsError:
        bucket_exists = False
        print("❌ R2 credentials not configured")
    except Exception as e:
        bucket_exists = False
        print(f"❌ R2 access check failed: {e}")

    if not bucket_exists:
        print()
        print("🔧 Infrastructure Setup Required:")
        print("   The R2 bucket needs to be created before deployment.")
        print("   Please run infrastructure deployment:")
        print("   1. Ensure R2 is enabled in your Cloudflare account")
        print("   2. Check API token has 'Account: Cloudflare R2:Edit' permission")
        print("   3. Run: python examples/deploy_infrastructure.py")
        print("   4. Or create R2 bucket manually in Cloudflare dashboard")
        print()
        print("Skipping R2 deployment for now...")
        print()
        return

    # Deploy site to R2
    result = await platform.deploy_tenant_site(
        tenant_id=tenant.tenant_id,
        local_path=folder_path,
    )

    if result.success:
        print("✅ Deployment successful!")
        print(f"   Files uploaded: {result.files_uploaded}")
        print(f"   Total size: {result.total_size_bytes} bytes")
        print(f"   Deployment time: {result.deployment_time_seconds:.2f}s")
    else:
        print(f"❌ Deployment failed: {result.error_message}")
        return

    print()

    # 3. Check worker script deployment
    print("3️⃣ Checking worker script deployment...")
    
    # Check if worker is deployed
    try:
        import httpx
        import os
        
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        worker_name = os.getenv("WORKER_SCRIPT_NAME", "getaipage-router")
        
        if account_id and api_token:
            worker_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{worker_name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    worker_url,
                    headers={"Authorization": f"Bearer {api_token}"},
                )
                
                if response.status_code == 200:
                    print(f"✅ Worker script '{worker_name}' is deployed")
                    print(f"   Route pattern: *.{domain_name}/*")
                    print(f"   R2 Bucket: {config.r2_bucket_name}")
                else:
                    print(f"⚠️  Worker script not found")
                    print(f"   To deploy worker: python deploy_worker.py")
        else:
            print(f"ℹ️  Worker verification skipped (credentials not available)")
    except Exception as e:
        print(f"ℹ️  Could not verify worker status: {e}")
        print(f"   Worker should be deployed via: python deploy_worker.py")

    print()

    # 4. Configure custom domain
    print("4️⃣ Configuring custom domain...")
    try:
        instructions = await platform.add_custom_domain(
            tenant_id=tenant.tenant_id,
            domain=domain_name,
        )
        print("✅ Custom domain added!")
        print(f"   Domain: {domain_name}")
        print(f"   Verification method: {instructions.verification_method}")
        print(f"   Instructions: {instructions.instructions}")
    except Exception as e:
        print(f"⚠️  Domain configuration failed: {e}")
        print("   Domain might already be configured or verification needed")

    print()

    # 5. Check domain status
    print("5️⃣ Checking domain configuration status...")
    try:
        domains = await platform.list_tenant_domains(tenant.tenant_id)
        domain_info = next((d for d in domains if d.domain == domain_name), None)

        if domain_info:
            print(f"✅ Domain status: {domain_info.status}")
            print(f"   Domain: {domain_info.domain}")
            print(f"   Created: {domain_info.created_at}")
            if hasattr(domain_info, 'verification_errors') and domain_info.verification_errors:
                print(f"   ⚠️  Verification errors: {domain_info.verification_errors}")
        else:
            print(f"❌ Domain {domain_name} not found in tenant domains")
    except Exception as e:
        print(f"⚠️  Domain status check failed: {e}")

    print()
    print("🎉 Deployment workflow completed!")
    print(f"   Tenant: {tenant.tenant_id}")
    print(f"   Subdomain: https://{tenant.subdomain}")
    print(f"   Custom domain: https://{domain_name} (after DNS verification)")


async def main():
    """Main entry point."""
    if len(sys.argv) != 4:
        print("Usage: python full_deployment_example.py <folder_path> <tenant_slug> <domain_name>")
        print()
        print("Example:")
        print("  python full_deployment_example.py ./my-website mytenant mytenant.com")
        sys.exit(1)

    folder_path = sys.argv[1]
    tenant_slug = sys.argv[2]
    domain_name = sys.argv[3]

    # Validate inputs
    if not Path(folder_path).exists():
        print(f"❌ Folder does not exist: {folder_path}")
        sys.exit(1)

    if not Path(folder_path).is_dir():
        print(f"❌ Path is not a directory: {folder_path}")
        sys.exit(1)

    # Configure logging
    configure_logging(
        level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_console=True,
    )

    # Load configuration from environment
    try:
        config = Config.from_env()
        print("✅ Configuration loaded from environment")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please set required environment variables:")
        print("  CLOUDFLARE_API_TOKEN")
        print("  CLOUDFLARE_ACCOUNT_ID")
        print("  CLOUDFLARE_ZONE_ID")
        print("  R2_ACCESS_KEY_ID")
        print("  R2_SECRET_ACCESS_KEY")
        print("  R2_BUCKET_NAME")
        print("  PLATFORM_DOMAIN")
        sys.exit(1)

    # Initialize platform
    storage = InMemoryStorageAdapter()
    platform = CloudflareSaaSPlatform(config, storage)

    try:
        await deploy_tenant_site(platform, folder_path, tenant_slug, domain_name, config)
    except KeyboardInterrupt:
        print("\n⚠️  Deployment interrupted by user")
    except Exception as e:
        print(f"❌ Deployment failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
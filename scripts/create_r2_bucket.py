#!/usr/bin/env python3
"""
Create R2 bucket directly using Cloudflare API.

This bypasses Terraform and creates the bucket directly.
"""

import asyncio
import json
import os
import sys

import httpx


async def create_r2_bucket(
    api_token: str,
    account_id: str,
    bucket_name: str,
    location: str = "WNAM"
) -> dict:
    """Create an R2 bucket."""
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    data = {
        "name": bucket_name,
        "locationHint": location
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return {
                "success": True,
                "bucket": response.json()["result"]
            }
        elif response.status_code == 409:
            # Bucket already exists
            return {
                "success": True,
                "exists": True,
                "message": "Bucket already exists"
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.json() if response.content else response.text
            }


async def list_r2_buckets(api_token: str, account_id: str) -> dict:
    """List R2 buckets."""
    
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code == 200:
            return {
                "success": True,
                "buckets": response.json()["result"]["buckets"]
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.json() if response.content else response.text
            }


async def main():
    """Main function."""
    
    # Load from environment
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    bucket_name = os.getenv("R2_BUCKET_NAME", "getaipage")
    
    if not api_token or not account_id:
        print("❌ Missing required environment variables:")
        print("   CLOUDFLARE_API_TOKEN")
        print("   CLOUDFLARE_ACCOUNT_ID")
        sys.exit(1)
    
    print("🪣 R2 Bucket Management")
    print("=" * 60)
    print(f"Account ID: {account_id}")
    print(f"Bucket Name: {bucket_name}")
    print()
    
    # List existing buckets
    print("📋 Listing existing R2 buckets...")
    list_result = await list_r2_buckets(api_token, account_id)
    
    if list_result["success"]:
        buckets = list_result["buckets"]
        if buckets:
            print(f"Found {len(buckets)} existing bucket(s):")
            for bucket in buckets:
                print(f"  - {bucket['name']} (Location: {bucket.get('location', 'N/A')}, Created: {bucket.get('creation_date', 'N/A')})")
        else:
            print("No existing buckets found.")
    else:
        print(f"⚠️  Failed to list buckets: {list_result.get('error', 'Unknown error')}")
    
    print()
    
    # Check if bucket already exists
    bucket_exists = False
    if list_result["success"]:
        bucket_exists = any(b["name"] == bucket_name for b in list_result["buckets"])
    
    if bucket_exists:
        print(f"✅ Bucket '{bucket_name}' already exists!")
        print()
        print("🎉 R2 bucket is ready for deployment!")
        print()
        print("Next steps:")
        print("  python examples/full_deployment_example.py /path/to/site tenant domain")
    else:
        # Create bucket
        print(f"🔨 Creating R2 bucket '{bucket_name}'...")
        create_result = await create_r2_bucket(api_token, account_id, bucket_name)
        
        if create_result["success"]:
            if create_result.get("exists"):
                print(f"✅ Bucket '{bucket_name}' already exists (confirmed)")
            else:
                bucket = create_result["bucket"]
                print(f"✅ Bucket created successfully!")
                print(f"   Name: {bucket['name']}")
                print(f"   Location: {bucket.get('location', 'N/A')}")
                print(f"   Created: {bucket.get('creation_date', 'N/A')}")
            
            print()
            print("🎉 R2 bucket is ready for deployment!")
            print()
            print("📝 Note: Your R2 credentials in .env should work now.")
            print()
            print("Next steps:")
            print("  1. Verify R2_ENDPOINT in .env is correct")
            print(f"     Should be: https://{account_id}.r2.cloudflarestorage.com")
            print("  2. Deploy infrastructure (Worker script):")
            print("     python examples/deploy_infrastructure.py")
            print("  3. Test full deployment:")
            print("     python examples/full_deployment_example.py /path/to/site tenant domain")
        else:
            print(f"❌ Failed to create bucket")
            print(f"Error: {json.dumps(create_result.get('error', 'Unknown error'), indent=2)}")
            print()
            print("💡 Troubleshooting:")
            print("1. Verify your API token has 'Account:Cloudflare R2:Edit' permission")
            print("2. Check that R2 is enabled for your account")
            print("3. Verify the bucket name is valid (lowercase, no special chars)")


if __name__ == "__main__":
    asyncio.run(main())

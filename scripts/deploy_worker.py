#!/usr/bin/env python3
"""
Deploy Cloudflare Worker Script via API

This script deploys the worker script to Cloudflare Workers using the API directly,
bypassing Terraform. It handles:
- Reading the worker template
- Creating/updating the worker script
- Binding R2 bucket
- Setting environment variables
- Creating worker routes
"""

import os
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
WORKER_SCRIPT_NAME = os.getenv("WORKER_SCRIPT_NAME", "getaipage-router")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "getaipage")
PLATFORM_DOMAIN = os.getenv("PLATFORM_DOMAIN", "getai.page")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "your-internal-api-key-here")

# API endpoints
BASE_URL = "https://api.cloudflare.com/client/v4"
WORKER_SCRIPT_URL = f"{BASE_URL}/accounts/{ACCOUNT_ID}/workers/scripts/{WORKER_SCRIPT_NAME}"
WORKER_ROUTES_URL = f"{BASE_URL}/zones/{ZONE_ID}/workers/routes"

def read_worker_script():
    """Read the worker script template"""
    script_path = Path(__file__).parent / "cloudflare_saas" / "worker_template.js"
    
    if not script_path.exists():
        print(f"❌ Worker script not found at: {script_path}")
        sys.exit(1)
    
    with open(script_path, 'r') as f:
        return f.read()

def create_worker_metadata():
    """Create worker metadata with R2 bindings and environment variables"""
    import json
    return json.dumps({
        "main_module": "index.js",
        "bindings": [
            {
                "type": "r2_bucket",
                "name": "MY_BUCKET",
                "bucket_name": R2_BUCKET_NAME
            }
        ],
        "compatibility_date": "2024-01-01",
        "compatibility_flags": ["nodejs_compat"],
        "vars": {
            "PLATFORM_DOMAIN": PLATFORM_DOMAIN,
            "INTERNAL_API_KEY": INTERNAL_API_KEY
        }
    })

async def deploy_worker_script():
    """Deploy worker script to Cloudflare"""
    print(f"🚀 Deploying worker script: {WORKER_SCRIPT_NAME}")
    print(f"   Account ID: {ACCOUNT_ID}")
    print(f"   R2 Bucket: {R2_BUCKET_NAME}")
    print()
    
    # Read worker script
    print("📖 Reading worker script...")
    worker_code = read_worker_script()
    print(f"   Script size: {len(worker_code)} bytes")
    print()
    
    # Create metadata
    metadata = create_worker_metadata()
    
    # Prepare multipart form data for worker upload
    # The Cloudflare API expects:
    # - metadata: JSON with bindings, vars, etc
    # - The module file(s)
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
        }
        
        # Create multipart form data with proper content disposition
        files = [
            ("metadata", (None, metadata, "application/json")),
            ("index.js", ("index.js", worker_code, "application/javascript+module")),
        ]
        
        print("📤 Uploading worker script to Cloudflare...")
        response = await client.put(
            WORKER_SCRIPT_URL,
            headers=headers,
            files=files,
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Worker script deployed successfully!")
                print()
                script_id = result.get("result", {}).get("id")
                if script_id:
                    print(f"   Script ID: {script_id}")
                return True
            else:
                print("❌ Worker deployment failed!")
                print(f"   Errors: {result.get('errors')}")
                return False
        else:
            print(f"❌ Worker deployment failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

async def create_worker_route(pattern="*"):
    """Create a worker route to handle all traffic on the zone"""
    print(f"🔗 Creating worker route...")
    print(f"   Pattern: {pattern}.{PLATFORM_DOMAIN}/*")
    print(f"   Worker: {WORKER_SCRIPT_NAME}")
    print()
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        }
        
        # First, list existing routes to avoid duplicates
        print("   Checking existing routes...")
        list_response = await client.get(
            WORKER_ROUTES_URL,
            headers=headers,
        )
        
        existing_routes = []
        if list_response.status_code == 200:
            result = list_response.json()
            if result.get("success"):
                existing_routes = result.get("result", [])
                print(f"   Found {len(existing_routes)} existing routes")
        
        # Check if route already exists
        route_pattern = f"{pattern}.{PLATFORM_DOMAIN}/*"
        existing_route = None
        for route in existing_routes:
            if route.get("pattern") == route_pattern:
                existing_route = route
                print(f"   ℹ️  Route already exists: {route.get('id')}")
                break
        
        if existing_route:
            # Update existing route
            route_id = existing_route.get("id")
            print(f"   Updating existing route: {route_id}")
            
            update_response = await client.put(
                f"{WORKER_ROUTES_URL}/{route_id}",
                headers=headers,
                json={
                    "pattern": route_pattern,
                    "script": WORKER_SCRIPT_NAME,
                }
            )
            
            if update_response.status_code == 200:
                result = update_response.json()
                if result.get("success"):
                    print("   ✅ Worker route updated successfully!")
                    return True
                else:
                    print(f"   ❌ Route update failed: {result.get('errors')}")
                    return False
            else:
                print(f"   ❌ Route update failed with status {update_response.status_code}")
                print(f"   Response: {update_response.text}")
                return False
        else:
            # Create new route
            print(f"   Creating new route...")
            
            create_response = await client.post(
                WORKER_ROUTES_URL,
                headers=headers,
                json={
                    "pattern": route_pattern,
                    "script": WORKER_SCRIPT_NAME,
                }
            )
            
            if create_response.status_code == 200:
                result = create_response.json()
                if result.get("success"):
                    print("   ✅ Worker route created successfully!")
                    route_id = result.get("result", {}).get("id")
                    if route_id:
                        print(f"   Route ID: {route_id}")
                    return True
                else:
                    print(f"   ❌ Route creation failed: {result.get('errors')}")
                    return False
            else:
                print(f"   ❌ Route creation failed with status {create_response.status_code}")
                print(f"   Response: {create_response.text}")
                return False

async def verify_worker_deployment():
    """Verify worker is deployed and accessible"""
    print()
    print("🔍 Verifying worker deployment...")
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
        }
        
        # Get worker details
        response = await client.get(
            WORKER_SCRIPT_URL,
            headers=headers,
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("success"):
                    print("✅ Worker is deployed and accessible")
                    worker_info = result.get("result", {})
                    print(f"   Script: {worker_info.get('id', 'N/A')}")
                    print(f"   Modified: {worker_info.get('modified_on', 'N/A')}")
                    return True
                else:
                    print(f"❌ Worker verification failed: {result.get('errors')}")
                    return False
            except Exception as e:
                # Response might be the script itself, not JSON
                print("✅ Worker is deployed (script content returned)")
                return True
        else:
            print(f"❌ Worker verification failed with status {response.status_code}")
            return False

async def main():
    """Main deployment workflow"""
    print("=" * 60)
    print("Cloudflare Worker Deployment")
    print("=" * 60)
    print()
    
    # Validate configuration
    if not all([API_TOKEN, ACCOUNT_ID, ZONE_ID]):
        print("❌ Missing required environment variables:")
        if not API_TOKEN:
            print("   - CLOUDFLARE_API_TOKEN")
        if not ACCOUNT_ID:
            print("   - CLOUDFLARE_ACCOUNT_ID")
        if not ZONE_ID:
            print("   - CLOUDFLARE_ZONE_ID")
        sys.exit(1)
    
    # Deploy worker script
    success = await deploy_worker_script()
    if not success:
        print()
        print("❌ Deployment failed at worker script upload")
        sys.exit(1)
    
    print()
    
    # Create worker route for wildcard subdomain
    route_success = await create_worker_route(pattern="*")
    if not route_success:
        print()
        print("⚠️  Warning: Worker route creation failed")
        print("   Worker is deployed but may not be accessible")
    
    # Verify deployment
    await verify_worker_deployment()
    
    print()
    print("=" * 60)
    print("🎉 Deployment Complete!")
    print("=" * 60)
    print()
    print("Worker Details:")
    print(f"   Name: {WORKER_SCRIPT_NAME}")
    print(f"   R2 Bucket: {R2_BUCKET_NAME}")
    print(f"   Route: *.{PLATFORM_DOMAIN}/*")
    print()
    print("Next Steps:")
    print(f"   1. Test worker: https://tenant-getaipage.{PLATFORM_DOMAIN}/")
    print(f"   2. Check logs: https://dash.cloudflare.com/{ACCOUNT_ID}/workers/services/view/{WORKER_SCRIPT_NAME}")
    print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

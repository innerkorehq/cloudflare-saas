#!/usr/bin/env python3
"""
Create Cloudflare D1 Database

This script creates a new D1 database in the specified jurisdiction.
"""

import os
import sys
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
D1_JURISDICTION = os.getenv("D1_JURISDICTION", "eu")
DATABASE_NAME = os.getenv("D1_DATABASE_NAME", "getaipage-domains")

# API endpoints
BASE_URL = "https://api.cloudflare.com/client/v4"
D1_CREATE_URL = f"{BASE_URL}/accounts/{ACCOUNT_ID}/d1/database"

async def create_d1_database():
    """Create a new D1 database"""
    print("🗄️  Creating D1 database...")
    print(f"   Account ID: {ACCOUNT_ID}")
    print(f"   Database Name: {DATABASE_NAME}")
    print(f"   Jurisdiction: {D1_JURISDICTION}")
    print()

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "name": DATABASE_NAME
        }

        # Add jurisdiction if specified
        if D1_JURISDICTION:
            payload["jurisdiction"] = D1_JURISDICTION

        response = await client.post(
            D1_CREATE_URL,
            headers=headers,
            json=payload,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                database = result.get("result", {})
                database_id = database.get("uuid")
                print("✅ D1 database created successfully!")
                print(f"   Database ID: {database_id}")
                print(f"   Database Name: {database.get('name')}")
                print(f"   Jurisdiction: {database.get('jurisdiction', 'default')}")
                print(f"   Created: {database.get('created_at')}")
                print()
                print("💡 Update your .env file:")
                print(f"D1_DATABASE_ID={database_id}")
                print()
                return database_id
            else:
                print("❌ Database creation failed!")
                print(f"   Errors: {result.get('errors')}")
                return None
        else:
            print(f"❌ D1 API request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None

async def list_d1_databases():
    """List existing D1 databases"""
    print("📋 Listing existing D1 databases...")
    print()

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
        }

        response = await client.get(
            D1_CREATE_URL,
            headers=headers,
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                databases = result.get("result", [])
                if not databases:
                    print("No D1 databases found.")
                    return []

                print(f"Found {len(databases)} D1 database(s):")
                print()

                for db in databases:
                    status = "✅" if db.get("status") == "active" else "❌"
                    print(f"  {status} {db.get('name')} (ID: {db.get('uuid')})")
                    print(f"     Jurisdiction: {db.get('jurisdiction', 'default')}")
                    print(f"     Status: {db.get('status')}")
                    print(f"     Created: {db.get('created_at')}")
                    print()

                return databases
            else:
                print(f"❌ Failed to list databases: {result.get('errors')}")
                return []
        else:
            print(f"❌ List request failed with status {response.status_code}")
            return []

async def main():
    """Main function"""
    print("=" * 60)
    print("Cloudflare D1 Database Creation")
    print("=" * 60)
    print()

    # Validate configuration
    if not all([API_TOKEN, ACCOUNT_ID]):
        print("❌ Missing required environment variables:")
        if not API_TOKEN:
            print("   - CLOUDFLARE_API_TOKEN")
        if not ACCOUNT_ID:
            print("   - CLOUDFLARE_ACCOUNT_ID")
        sys.exit(1)

    # List existing databases first
    existing_dbs = await list_d1_databases()

    # Check if database already exists
    existing_db = None
    for db in existing_dbs:
        if db.get("name") == DATABASE_NAME:
            existing_db = db
            break

    if existing_db:
        print(f"ℹ️  Database '{DATABASE_NAME}' already exists!")
        print(f"   Database ID: {existing_db.get('uuid')}")
        print()
        print("💡 Update your .env file:")
        print(f"D1_DATABASE_ID={existing_db.get('uuid')}")
        print()
        return

    # Create new database
    database_id = await create_d1_database()

    if database_id:
        print("=" * 60)
        print("🎉 D1 Database Creation Complete!")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("   1. Update your .env file with the database ID")
        print("   2. Run: python scripts/create_d1_tables.py")
        print("   3. Run: python scripts/deploy_worker.py")
        print()
    else:
        print()
        print("❌ Database creation failed")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check if D1 is enabled for your account")
        print("   2. Verify your API token has D1 permissions")
        print("   3. Try creating the database manually in the Cloudflare dashboard")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

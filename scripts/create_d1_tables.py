#!/usr/bin/env python3
"""
Create D1 Database Tables for Cloudflare SaaS

This script creates the necessary tables in Cloudflare D1 database:
- domains table with auto-managed timestamps
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
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
D1_DATABASE_ID = os.getenv("D1_DATABASE_ID")
D1_JURISDICTION = os.getenv("D1_JURISDICTION", "eu")

# API endpoints
BASE_URL = "https://api.cloudflare.com/client/v4"
D1_QUERY_URL = f"{BASE_URL}/accounts/{ACCOUNT_ID}/d1/database/{D1_DATABASE_ID}/query"

def create_domains_table_sql():
    """Generate SQL to create domains table with auto-managed timestamps"""
    return f"""
-- Create domains table
CREATE TABLE IF NOT EXISTS domains (
    name TEXT NOT NULL,
    zone TEXT NOT NULL DEFAULT '{ZONE_ID}',
    tenant_id TEXT NOT NULL,
    created DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_date DATETIME,
    PRIMARY KEY (name, zone)
);

-- Create trigger to auto-update 'updated' timestamp
CREATE TRIGGER IF NOT EXISTS update_domains_updated
    AFTER UPDATE ON domains
    FOR EACH ROW
    BEGIN
        UPDATE domains SET updated = CURRENT_TIMESTAMP WHERE name = NEW.name AND zone = NEW.zone;
    END;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_domains_tenant_id ON domains(tenant_id);
CREATE INDEX IF NOT EXISTS idx_domains_zone ON domains(zone);

-- Insert initial data
INSERT OR IGNORE INTO domains (name, zone, tenant_id) VALUES ('www.botshub.com', '{ZONE_ID}', 'tenant-finaldemo');
"""

async def execute_d1_query(sql):
    """Execute SQL query on D1 database"""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "sql": sql,
            "params": []
        }

        response = await client.post(
            D1_QUERY_URL,
            headers=headers,
            json=payload,
        )

        return response

async def create_domains_table():
    """Create the domains table in D1"""
    print("🗄️  Creating domains table in D1 database...")
    print(f"   Database ID: {D1_DATABASE_ID}")
    print(f"   Jurisdiction: {D1_JURISDICTION}")
    print()

    # Get SQL for table creation
    sql = create_domains_table_sql()

    # Execute the query
    response = await execute_d1_query(sql)

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ Domains table created successfully!")
            print()

            # Show results
            for query_result in result.get("result", []):
                if query_result.get("success"):
                    changes = query_result.get("meta", {}).get("changes", 0)
                    duration = query_result.get("meta", {}).get("duration", 0)
                    print(f"   Query executed: {changes} changes, {duration}ms")
                else:
                    print(f"   ⚠️  Query warning: {query_result.get('results', [])}")
            # Check if initial data was inserted
            if any(query_result.get("meta", {}).get("changes", 0) > 0 for query_result in result.get("result", [])):
                print("   ✅ Initial domain data inserted")
            
            return True
        else:
            print("❌ Table creation failed!")
            print(f"   Errors: {result.get('errors')}")
            return False
    else:
        print(f"❌ D1 API request failed with status {response.status_code}")
        print(f"   Response: {response.text}")
        return False

async def verify_table_creation():
    """Verify the table was created correctly"""
    print()
    print("🔍 Verifying table creation...")

    # Query to check table structure
    sql = """
    PRAGMA table_info(domains);
    SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table' AND name='domains';
    SELECT sql FROM sqlite_master WHERE type='trigger' AND name='update_domains_updated';
    """

    response = await execute_d1_query(sql)

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ Table verification successful!")

            # Parse results
            queries = result.get("result", [])
            if len(queries) >= 3:
                # Table info
                table_info = queries[0].get("results", [])
                print(f"   Table columns: {len(table_info)}")
                for col in table_info:
                    print(f"     - {col['name']} ({col['type']}) {'PRIMARY KEY' if col.get('pk') else ''}")

                # Table count
                table_count = queries[1].get("results", [])
                if table_count and table_count[0].get("table_count", 0) > 0:
                    print("   ✅ Table exists")
                else:
                    print("   ❌ Table does not exist")

                # Trigger check
                trigger_info = queries[2].get("results", [])
                if trigger_info:
                    print("   ✅ Update trigger exists")
                else:
                    print("   ❌ Update trigger missing")

            return True
        else:
            print(f"❌ Verification failed: {result.get('errors')}")
            return False
    else:
        print(f"❌ Verification request failed with status {response.status_code}")
        return False

async def main():
    """Main setup workflow"""
    print("=" * 60)
    print("Cloudflare D1 Database Setup")
    print("=" * 60)
    print()

    # Validate configuration
    if not all([API_TOKEN, ACCOUNT_ID, D1_DATABASE_ID]):
        print("❌ Missing required environment variables:")
        if not API_TOKEN:
            print("   - CLOUDFLARE_API_TOKEN")
        if not ACCOUNT_ID:
            print("   - CLOUDFLARE_ACCOUNT_ID")
        if not D1_DATABASE_ID:
            print("   - D1_DATABASE_ID")
        print()
        print("Please update your .env file with the correct values.")
        sys.exit(1)

    # Create domains table
    success = await create_domains_table()
    if not success:
        print()
        print("❌ Setup failed at table creation")
        sys.exit(1)

    # Verify setup
    await verify_table_creation()

    print()
    print("=" * 60)
    print("🎉 D1 Database Setup Complete!")
    print("=" * 60)
    print()
    print("Database Details:")
    print(f"   Database ID: {D1_DATABASE_ID}")
    print(f"   Jurisdiction: {D1_JURISDICTION}")
    print()
    print("Table Schema:")
    print("   domains (name, zone, tenant_id, created, updated, last_date)")
    print("   - Primary Key: (name, zone)")
    print("   - Auto-managed: created, updated timestamps")
    print("   - Indexes: tenant_id, zone")
    print("   - Initial data: www.botshub.com -> tenant-finaldemo")
    print()
    print("Next Steps:")
    print("   1. Test worker deployment: python ./scripts/deploy_worker.py")
    print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

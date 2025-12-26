# Cloudflare SaaS Scripts

This folder contains the working scripts for deploying and managing the Cloudflare SaaS platform.

## Scripts Overview

### 1. `deploy_worker.py`
**Purpose:** Deploy Cloudflare Worker script via API  
**Usage:** `python scripts/deploy_worker.py`  
**What it does:**
- Reads worker template from `cloudflare_saas/worker_template_d1.js`
- Creates metadata with R2 and D1 bindings and environment variables
- Uploads worker as ES module to Cloudflare
- Creates/updates worker route for `*.getai.page/*`
- Verifies deployment

### 1.5. `create_d1_tables.py`
**Purpose:** Create database tables in Cloudflare D1  
**Usage:** `python scripts/create_d1_tables.py`  
**What it does:**
- Creates `domains` table with auto-managed timestamps
- Sets up triggers for automatic `updated` field management
- Creates indexes for performance
- Verifies table creation

**Database Schema:**
```sql
CREATE TABLE domains (
    name TEXT NOT NULL,           -- Domain name (primary key part 1)
    zone TEXT NOT NULL DEFAULT '{CLOUDFLARE_ZONE_ID}',  -- Zone (primary key part 2, from env)
    tenant_id TEXT NOT NULL,      -- Associated tenant ID
    created DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Auto-managed
    updated DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Auto-managed via trigger
    last_date DATETIME,           -- Manual last access date
    PRIMARY KEY (name, zone)
);

-- Initial data inserted:
-- www.botshub.com -> tenant-finaldemo
```

### 2. `create_token_with_global_key.py`
**Purpose:** Create API tokens with proper permissions using Global API Key  
**Usage:** `python scripts/create_token_with_global_key.py`  
**What it does:**
- Uses Global API Key for token creation (more reliable)
- Creates User API token with 8 required permissions:
  - Account Settings Read
  - Workers R2 Storage Write
  - Workers Scripts Read/Write
  - Workers Routes Write
  - Zone Read
  - SSL and Certificates Read/Write
- Tests token permissions automatically

### 3. `create_r2_bucket.py`
**Purpose:** Create and manage R2 buckets via Cloudflare API  
**Usage:** `python scripts/create_r2_bucket.py`  
**What it does:**
- Creates R2 buckets in specified location
- Lists existing R2 buckets
- Verifies bucket creation

### 4. `test_token_permissions.py`
**Purpose:** Test API token permissions comprehensively  
**Usage:** `python scripts/test_token_permissions.py`  
**What it does:**
- Tests 8 permission categories:
  - Basic authentication
  - Account access
  - Zone access
  - R2 operations (list/create)
  - Workers operations (list/routes)
  - Custom hostnames
- Reports pass/fail for each test

## Quick Usage

### Full Deployment Workflow

```bash
# 1. Test token permissions
python scripts/test_token_permissions.py

# 2. Create R2 bucket (if needed)
python scripts/create_r2_bucket.py

# 3. Create D1 tables
python scripts/create_d1_tables.py

# 4. Deploy worker
python scripts/deploy_worker.py

# 5. Run full deployment example
python examples/full_deployment_example.py <folder> <tenant> <domain>
```

### Create New API Token

```bash
# Requires Global API Key in .env
python scripts/create_token_with_global_key.py
```

## Environment Requirements

All scripts require these environment variables in `.env`:

```env
# Cloudflare API
CLOUDFLARE_API_TOKEN=<your-working-token>
CLOUDFLARE_ACCOUNT_ID=6451353ea5a8407bab6162abc42f5338
CLOUDFLARE_ZONE_ID=2cf1f02313c4ef76af3d62eb78bb906e

# R2 Storage
R2_BUCKET_NAME=getaipage
R2_JURISDICTION=eu
R2_ENDPOINT=https://6451353ea5a8407bab6162abc42f5338.eu.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<your-key>
R2_SECRET_ACCESS_KEY=<your-secret>

# D1 Database
D1_DATABASE_ID=<your-d1-database-id>
D1_JURISDICTION=eu

# Platform
PLATFORM_DOMAIN=getai.page
WORKER_SCRIPT_NAME=getaipage-router
WORKER_SCRIPT_TEMPLATE_NAME=worker_template_d1.js
```

## Dependencies

```bash
pip install httpx python-dotenv boto3
```

## Notes

- These scripts were tested and confirmed working
- All scripts use async/await with httpx for API calls
- Error handling and logging included
- Scripts validate environment variables before running

## Related Files

- `examples/full_deployment_example.py` - Complete tenant deployment workflow
- `cloudflare_saas/worker_template.js` - Worker script template
- `docs/DNS_SETUP_GUIDE.md` - DNS configuration instructions
- `docs/COMPLETE_SYSTEM.md` - Full system documentation
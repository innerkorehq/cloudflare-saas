# Cloudflare SaaS Scripts

This folder contains the working scripts for deploying and managing the Cloudflare SaaS platform.

## Scripts Overview

### 1. `deploy_worker.py`
**Purpose:** Deploy Cloudflare Worker script via API  
**Usage:** `python scripts/deploy_worker.py`  
**What it does:**
- Reads worker template from `cloudflare_saas/worker_template.js`
- Creates metadata with R2 bindings and environment variables
- Uploads worker as ES module to Cloudflare
- Creates/updates worker route for `*.getai.page/*`
- Verifies deployment

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

# 3. Deploy worker
python scripts/deploy_worker.py

# 4. Run full deployment example
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
R2_ENDPOINT=https://6451353ea5a8407bab6162abc42f5338.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<your-key>
R2_SECRET_ACCESS_KEY=<your-secret>

# Platform
PLATFORM_DOMAIN=getai.page
WORKER_SCRIPT_NAME=getaipage-router
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
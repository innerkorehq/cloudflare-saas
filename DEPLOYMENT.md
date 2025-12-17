# Deployment Guide

This guide covers deploying the Cloudflare SaaS platform in production.

## Prerequisites

1. **Cloudflare Account**
   - API Token with permissions for:
     - Zone:Read, Zone:Edit
     - DNS:Edit
     - Workers:Edit
     - R2:Read, R2:Edit
     - Custom Hostnames:Read, Custom Hostnames:Edit
   - Account ID and Zone ID
   - R2 access credentials

2. **Infrastructure**
   - PostgreSQL database (or use in-memory for testing)
   - Server/container platform (AWS, GCP, Azure, etc.)
   - Terraform CLI (for infrastructure deployment)

3. **Domain**
   - A registered domain for your platform (e.g., yourplatform.com)
   - DNS configured to use Cloudflare

## Step 1: Environment Setup

Create `.env` file with required variables:

```bash
# Copy example and fill in values
cp .env.example .env

# Edit with your credentials
nano .env
```

Required variables:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_ZONE_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `PLATFORM_DOMAIN`

Optional:
- `DATABASE_URL` (for PostgreSQL)
- `INTERNAL_API_KEY` (for Worker authentication)

## Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e ".[web]"
```

## Step 3: Deploy Infrastructure

```bash
# Deploy R2 bucket and Worker
python examples/deploy_infrastructure.py
```

This will:
- Create R2 bucket
- Deploy Worker script to Cloudflare
- Configure Worker routes

## Step 4: Database Setup (PostgreSQL)

If using PostgreSQL storage:

```bash
# Initialize database
python -c "
import asyncio
from cloudflare_saas import PostgresStorageAdapter
import os

async def init():
    storage = PostgresStorageAdapter(os.getenv('DATABASE_URL'))
    await storage.initialize()
    await storage.close()
    print('Database initialized')

asyncio.run(init())
"
```

## Step 5: Deploy API

### Option A: Docker

```bash
# Build image
docker build -t cloudflare-saas-api .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name saas-api \
  cloudflare-saas-api
```

### Option B: Docker Compose

```bash
docker-compose up -d
```

### Option C: Direct Python

```bash
# Run with uvicorn
uvicorn examples.fastapi_integration:app --host 0.0.0.0 --port 8000
```

### Option D: Production WSGI Server

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn examples.fastapi_integration:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Step 6: Configure Cloudflare DNS

Add DNS record for your API:

```
Type: A
Name: api
Value: <your-server-ip>
Proxied: Yes
```

## Step 7: Verify Deployment

```bash
# Health check
curl https://api.yourplatform.com/health

# Create test tenant
curl -X POST https://api.yourplatform.com/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Company", "slug": "test-co"}'
```

## Step 8: Production Checklist

- [ ] Environment variables secured (use secrets manager)
- [ ] Database backups configured
- [ ] Monitoring and logging setup
- [ ] Rate limiting enabled
- [ ] Authentication/authorization implemented
- [ ] SSL/TLS certificates valid
- [ ] Worker script deployed and tested
- [ ] R2 bucket configured with proper access controls
- [ ] DNS records propagated
- [ ] Load balancer configured (if using multiple servers)

## Monitoring

Key metrics to monitor:
- API response times
- R2 upload/download operations
- Custom hostname provisioning success rate
- DNS verification times
- Worker invocation count
- Database connection pool status

## Scaling

### Horizontal Scaling
- Run multiple API instances behind load balancer
- Use PostgreSQL for shared state
- Cache host->tenant mappings in Worker KV or Redis

### Performance Optimization
- Enable CDN caching for static assets
- Use Worker caching for repeated lookups
- Implement connection pooling for database
- Batch R2 operations where possible

## Backup and Recovery

### Database Backups
```bash
# Automated backup script
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### R2 Backups
- Enable R2 bucket versioning
- Regular sync to backup location
- Test restore procedures

## Troubleshooting

### Worker Not Serving Files
- Verify R2 binding in Worker configuration
- Check Worker logs in Cloudflare dashboard
- Verify tenant objects exist in R2

### Domain Verification Failing
- Check DNS propagation: `dig www.customer.com`
- Verify CNAME points to correct target
- Check Cloudflare dashboard for SSL status

### API Errors
- Check application logs
- Verify environment variables
- Test database connectivity
- Check Cloudflare API rate limits

## Security Best Practices

1. **API Keys**
   - Rotate regularly
   - Use least-privilege permissions
   - Store in secrets manager

2. **Database**
   - Use SSL connections
   - Implement row-level security
   - Regular security updates

3. **Worker**
   - Validate all inputs
   - Implement rate limiting
   - Log security events

4. **Custom Domains**
   - Verify ownership before activation
   - Monitor for abuse
   - Implement domain blocklists

## Package Publishing

The library is automatically published to PyPI and ReadTheDocs when a new release is created on GitHub.

### Setup

1. **PyPI API Token**
   - Go to https://pypi.org/manage/account/
   - Create an API token
   - Add to GitHub repository secrets as `PYPI_API_TOKEN`

2. **ReadTheDocs Token**
   - Go to https://readthedocs.org/accounts/tokens/
   - Create a token
   - Add to GitHub repository secrets as `RTD_TOKEN`

### Release Process

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create a new GitHub release with the version tag (e.g., `v1.0.0`)
4. The workflow will automatically:
   - Build the package
   - Publish to PyPI
   - Trigger ReadTheDocs build

## Support

For issues or questions:
- Check logs: `docker logs saas-api`
- Review Cloudflare dashboard
- Check database connectivity
- Verify environment variables
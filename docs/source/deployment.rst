Deployment
==========

Guide for deploying the Cloudflare SaaS Platform in production environments.

Infrastructure Requirements
----------------------------

Cloudflare Services
^^^^^^^^^^^^^^^^^^^

Required Cloudflare services:

1. **R2 Bucket**: For storing tenant static sites
2. **Custom Hostname Zone**: For managing custom domains
3. **Workers** (optional): For advanced routing

Database (Optional)
^^^^^^^^^^^^^^^^^^^

For production deployments, use PostgreSQL:

- PostgreSQL 12+ recommended
- Connection pooling recommended
- Asyncpg driver required

Deployment Options
------------------

Docker Deployment
^^^^^^^^^^^^^^^^^

Using Docker Compose:

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   
   services:
     api:
       build: .
       ports:
         - "8000:8000"
       environment:
         - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
         - CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID}
         - CLOUDFLARE_ZONE_ID=${CLOUDFLARE_ZONE_ID}
         - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
         - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
         - R2_BUCKET_NAME=${R2_BUCKET_NAME}
         - PLATFORM_DOMAIN=${PLATFORM_DOMAIN}
         - DATABASE_URL=${DATABASE_URL}
         - LOG_LEVEL=INFO
         - LOG_FORMAT=json
       depends_on:
         - db
     
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: cloudflare_saas
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: ${DB_PASSWORD}
       volumes:
         - postgres_data:/var/lib/postgresql/data
   
   volumes:
     postgres_data:

Dockerfile:

.. code-block:: dockerfile

   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY cloudflare_saas ./cloudflare_saas
   COPY examples ./examples

   CMD ["uvicorn", "examples.fastapi_integration:app", "--host", "0.0.0.0", "--port", "8000"]

Kubernetes Deployment
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   # deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: cloudflare-saas-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: cloudflare-saas-api
     template:
       metadata:
         labels:
           app: cloudflare-saas-api
       spec:
         containers:
         - name: api
           image: your-registry/cloudflare-saas:latest
           ports:
           - containerPort: 8000
           env:
           - name: CLOUDFLARE_API_TOKEN
             valueFrom:
               secretKeyRef:
                 name: cloudflare-secrets
                 key: api-token
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: db-secrets
                 key: url
           - name: LOG_LEVEL
             value: "INFO"
           - name: LOG_FORMAT
             value: "json"
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: cloudflare-saas-api
   spec:
     selector:
       app: cloudflare-saas-api
     ports:
     - port: 80
       targetPort: 8000
     type: LoadBalancer

Serverless Deployment
^^^^^^^^^^^^^^^^^^^^^

For AWS Lambda with API Gateway:

.. code-block:: python

   # lambda_handler.py
   from mangum import Mangum
   from examples.fastapi_integration import app

   handler = Mangum(app)

Configuration
-------------

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

Production environment variables:

.. code-block:: bash

   # Required
   CLOUDFLARE_API_TOKEN=your-token
   CLOUDFLARE_ACCOUNT_ID=your-account
   CLOUDFLARE_ZONE_ID=your-zone
   R2_ACCESS_KEY_ID=your-key
   R2_SECRET_ACCESS_KEY=your-secret
   R2_BUCKET_NAME=production-sites
   PLATFORM_DOMAIN=yourplatform.com
   
   # Database
   DATABASE_URL=postgresql://user:pass@db:5432/cloudflare_saas
   
   # Logging
   LOG_LEVEL=WARNING
   LOG_FORMAT=json
   LOG_FILE=/var/log/cloudflare-saas/app.log
   ENABLE_CONSOLE_LOGGING=false
   
   # Optional
   WORKER_SCRIPT_NAME=site-router
   INTERNAL_API_KEY=your-internal-key

Secrets Management
^^^^^^^^^^^^^^^^^^

Use a secrets manager in production:

.. code-block:: python

   # Example with AWS Secrets Manager
   import boto3
   import json
   from cloudflare_saas import Config

   def load_config_from_secrets():
       client = boto3.client('secretsmanager')
       secret = client.get_secret_value(SecretId='cloudflare-saas/prod')
       secrets = json.loads(secret['SecretString'])
       
       return Config(
           cloudflare_api_token=secrets['cloudflare_api_token'],
           cloudflare_account_id=secrets['cloudflare_account_id'],
           # ... other config
       )

Database Setup
--------------

PostgreSQL Initialization
^^^^^^^^^^^^^^^^^^^^^^^^^

Run migrations:

.. code-block:: bash

   # Install alembic
   pip install alembic

   # Initialize (first time only)
   alembic init alembic

   # Create migration
   alembic revision --autogenerate -m "Initial schema"

   # Apply migrations
   alembic upgrade head

Using with Application:

.. code-block:: python

   from cloudflare_saas import (
       CloudflareSaaSPlatform,
       Config,
       PostgresStorageAdapter
   )

   async def init_platform():
       config = Config.from_env()
       
       storage = await PostgresStorageAdapter.create(
           config.database_url
       )
       
       platform = CloudflareSaaSPlatform(config, storage=storage)
       return platform

Monitoring and Logging
-----------------------

Structured Logging
^^^^^^^^^^^^^^^^^^

Configure for log aggregation:

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel, LogFormat

   configure_logging(
       level=LogLevel.INFO,
       log_format=LogFormat.JSON,
       enable_console=True,  # For container logs
       log_file=None
   )

Log Aggregation
^^^^^^^^^^^^^^^

Example Filebeat configuration:

.. code-block:: yaml

   filebeat.inputs:
   - type: container
     paths:
       - '/var/lib/docker/containers/*/*.log'
     
     processors:
     - add_docker_metadata:
         host: "unix:///var/run/docker.sock"
     
     - decode_json_fields:
         fields: ["message"]
         target: ""
         overwrite_keys: true

   output.elasticsearch:
     hosts: ["elasticsearch:9200"]

Health Checks
^^^^^^^^^^^^^

Implement health check endpoints:

.. code-block:: python

   from fastapi import FastAPI
   from cloudflare_saas import CloudflareSaaSPlatform

   app = FastAPI()

   @app.get("/health")
   async def health_check():
       return {"status": "healthy"}

   @app.get("/health/ready")
   async def readiness_check():
       # Check database connection
       # Check Cloudflare API
       return {"status": "ready"}

Performance Optimization
------------------------

Connection Pooling
^^^^^^^^^^^^^^^^^^

For PostgreSQL:

.. code-block:: python

   from cloudflare_saas import PostgresStorageAdapter
   
   storage = await PostgresStorageAdapter.create(
       database_url,
       min_size=10,
       max_size=100
   )

Caching
^^^^^^^

Implement caching for frequently accessed data:

.. code-block:: python

   from functools import lru_cache
   
   class CachedPlatform:
       def __init__(self, platform):
           self.platform = platform
       
       @lru_cache(maxsize=1000)
       async def get_tenant_cached(self, tenant_id):
           return await self.platform.get_tenant(tenant_id)

Scaling Considerations
----------------------

Horizontal Scaling
^^^^^^^^^^^^^^^^^^

The platform is stateless and can be scaled horizontally:

- Deploy multiple instances behind a load balancer
- Share database connection pool across instances
- Use Redis for distributed caching (optional)

Rate Limiting
^^^^^^^^^^^^^

Implement rate limiting for API endpoints:

.. code-block:: python

   from fastapi import FastAPI
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)
   app = FastAPI()
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

   @app.post("/tenants")
   @limiter.limit("10/minute")
   async def create_tenant(request: Request):
       # ...

Security Best Practices
-----------------------

1. **API Token Security**: Never commit tokens to version control
2. **TLS/SSL**: Use HTTPS for all API endpoints
3. **Input Validation**: Validate all user inputs
4. **Rate Limiting**: Protect against abuse
5. **Audit Logging**: Log all administrative actions
6. **Access Control**: Implement proper authentication/authorization

Backup and Recovery
-------------------

Database Backups
^^^^^^^^^^^^^^^^

Automated PostgreSQL backups:

.. code-block:: bash

   # Daily backup script
   #!/bin/bash
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   pg_dump cloudflare_saas > backup_$TIMESTAMP.sql
   
   # Upload to cloud storage
   aws s3 cp backup_$TIMESTAMP.sql s3://backups/

R2 Data Recovery
^^^^^^^^^^^^^^^^

R2 objects are durable, but implement versioning:

.. code-block:: python

   # Enable versioning on bucket (do once)
   # Then access previous versions if needed

Troubleshooting
---------------

Common Issues
^^^^^^^^^^^^^

**Database Connection Errors**

- Check DATABASE_URL format
- Verify network connectivity
- Check connection pool settings

**R2 Upload Failures**

- Verify R2 credentials
- Check bucket permissions
- Monitor rate limits

**Custom Hostname Issues**

- Verify zone_id is correct
- Check DNS configuration
- Review Cloudflare dashboard

Monitoring Commands
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check Docker logs
   docker-compose logs -f api

   # Check Kubernetes pods
   kubectl logs -f deployment/cloudflare-saas-api

   # Database connection count
   psql -c "SELECT count(*) FROM pg_stat_activity"

See Also
--------

- :doc:`configuration` - Configuration guide
- :doc:`logging` - Logging setup
- :doc:`examples` - Code examples

Examples
========

Practical examples for common use cases.

Basic Examples
--------------

Creating and Managing Tenants
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from cloudflare_saas import CloudflareSaaSPlatform, Config, configure_logging, LogLevel

   async def main():
       # Configure logging
       configure_logging(level=LogLevel.INFO)
       
       # Load configuration
       config = Config.from_env()
       platform = CloudflareSaaSPlatform(config)
       
       # Create a new tenant
       tenant = await platform.create_tenant(
           name="Acme Corporation",
           slug="acme",
           owner_id="user_12345",
           metadata={
               "plan": "enterprise",
               "industry": "technology"
           }
       )
       
       print(f"Tenant ID: {tenant.tenant_id}")
       print(f"Subdomain: {tenant.subdomain}")
       
       # Get tenant by ID
       retrieved_tenant = await platform.get_tenant(tenant.tenant_id)
       print(f"Retrieved: {retrieved_tenant.name}")
       
       # List all tenants
       tenants = await platform.list_tenants(limit=10)
       print(f"Total tenants: {len(tenants)}")

   if __name__ == "__main__":
       asyncio.run(main())

Site Deployment
^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from pathlib import Path
   from cloudflare_saas import CloudflareSaaSPlatform, Config

   async def deploy_site():
       config = Config.from_env()
       platform = CloudflareSaaSPlatform(config)
       
       tenant = await platform.get_tenant("tenant-acme")
       
       # Deploy a static website
       result = await platform.deploy_tenant_site(
           tenant_id=tenant.tenant_id,
           local_path="./dist",  # Path to built site
           base_prefix="v1"  # Optional prefix for versioning
       )
       
       if result.success:
           print(f"✓ Deployment successful!")
           print(f"  Files uploaded: {result.files_uploaded}")
           print(f"  Total size: {result.total_size_bytes / 1024 / 1024:.2f} MB")
           print(f"  Time: {result.deployment_time_seconds:.2f}s")
           print(f"  Site available at: https://{tenant.subdomain}")
       else:
           print(f"✗ Deployment failed: {result.error_message}")

   if __name__ == "__main__":
       asyncio.run(deploy_site())

Custom Domain Management
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from cloudflare_saas import CloudflareSaaSPlatform, Config

   async def setup_custom_domain():
       config = Config.from_env()
       platform = CloudflareSaaSPlatform(config)
       
       tenant_id = "tenant-acme"
       custom_domain = "www.acme.com"
       
       # Add custom domain
       domain_status = await platform.add_custom_domain(
           tenant_id=tenant_id,
           domain=custom_domain
       )
       
       print(f"Domain: {domain_status.domain}")
       print(f"Status: {domain_status.status}")
       print(f"SSL Status: {domain_status.ssl_status}")
       
       # Get verification instructions
       instructions = await platform.get_domain_verification_instructions(
           custom_domain
       )
       
       print(f"\\nVerification Method: {instructions.verification_method}")
       print(f"Instructions: {instructions.instructions}")
       
       # Wait and check status
       import time
       for i in range(10):
           await asyncio.sleep(30)  # Check every 30 seconds
           
           status = await platform.get_custom_domain_status(custom_domain)
           print(f"Check {i+1}: {status.status}, SSL: {status.ssl_status}")
           
           if status.status == "active" and status.ssl_status == "active":
               print("✓ Domain is fully active!")
               break

   if __name__ == "__main__":
       asyncio.run(setup_custom_domain())

Advanced Examples
-----------------

Using PostgreSQL Storage
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from cloudflare_saas import (
       CloudflareSaaSPlatform,
       Config,
       PostgresStorageAdapter
   )

   async def main():
       config = Config.from_env()
       
       # Initialize PostgreSQL storage
       storage = await PostgresStorageAdapter.create(
           "postgresql://user:pass@localhost/cloudflare_saas"
       )
       
       # Use with platform
       platform = CloudflareSaaSPlatform(config, storage=storage)
       
       # Now all tenant/domain data is persisted in PostgreSQL
       tenant = await platform.create_tenant("Example", "example")
       
       # Clean up
       await storage.close()

   if __name__ == "__main__":
       asyncio.run(main())

Batch Operations
^^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from cloudflare_saas import CloudflareSaaSPlatform, Config

   async def batch_deploy():
       config = Config.from_env()
       platform = CloudflareSaaSPlatform(config)
       
       # Define tenants to deploy
       tenants_to_deploy = [
           ("tenant-acme", "./sites/acme"),
           ("tenant-widgets", "./sites/widgets"),
           ("tenant-gadgets", "./sites/gadgets"),
       ]
       
       # Deploy all concurrently
       tasks = [
           platform.deploy_tenant_site(tenant_id, path)
           for tenant_id, path in tenants_to_deploy
       ]
       
       results = await asyncio.gather(*tasks, return_exceptions=True)
       
       # Report results
       for (tenant_id, _), result in zip(tenants_to_deploy, results):
           if isinstance(result, Exception):
               print(f"✗ {tenant_id}: {result}")
           elif result.success:
               print(f"✓ {tenant_id}: {result.files_uploaded} files")
           else:
               print(f"✗ {tenant_id}: {result.error_message}")

   if __name__ == "__main__":
       asyncio.run(batch_deploy())

Error Handling
^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from cloudflare_saas import (
       CloudflareSaaSPlatform,
       Config,
       TenantNotFoundError,
       DeploymentError,
       DomainVerificationError,
   )

   async def handle_errors():
       config = Config.from_env()
       platform = CloudflareSaaSPlatform(config)
       
       # Tenant not found
       try:
           tenant = await platform.get_tenant("nonexistent")
       except TenantNotFoundError as e:
           print(f"Tenant error: {e}")
       
       # Deployment error
       try:
           result = await platform.deploy_tenant_site(
               "tenant-acme",
               "/invalid/path"
           )
       except DeploymentError as e:
           print(f"Deployment error: {e}")
       
       # Domain verification error
       try:
           status = await platform.add_custom_domain(
               "tenant-acme",
               "invalid-domain"
           )
       except DomainVerificationError as e:
           print(f"Domain error: {e}")

   if __name__ == "__main__":
       asyncio.run(handle_errors())

FastAPI Integration
-------------------

Complete FastAPI Application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from fastapi import FastAPI, HTTPException, Depends
   from pydantic import BaseModel
   from cloudflare_saas import (
       CloudflareSaaSPlatform,
       Config,
       configure_logging,
       LogLevel,
       TenantNotFoundError,
   )

   # Configure logging
   configure_logging(level=LogLevel.INFO)

   # Initialize platform
   config = Config.from_env()
   platform = CloudflareSaaSPlatform(config)

   app = FastAPI(title="SaaS Platform API")

   # Request models
   class CreateTenantRequest(BaseModel):
       name: str
       slug: str
       owner_id: str | None = None

   class AddDomainRequest(BaseModel):
       domain: str

   # Endpoints
   @app.post("/tenants")
   async def create_tenant(request: CreateTenantRequest):
       tenant = await platform.create_tenant(
           name=request.name,
           slug=request.slug,
           owner_id=request.owner_id
       )
       return tenant

   @app.get("/tenants/{tenant_id}")
   async def get_tenant(tenant_id: str):
       try:
           tenant = await platform.get_tenant(tenant_id)
           return tenant
       except TenantNotFoundError:
           raise HTTPException(status_code=404, detail="Tenant not found")

   @app.get("/tenants")
   async def list_tenants(limit: int = 100, offset: int = 0):
       tenants = await platform.list_tenants(limit, offset)
       return {"tenants": tenants, "count": len(tenants)}

   @app.post("/tenants/{tenant_id}/domains")
   async def add_custom_domain(tenant_id: str, request: AddDomainRequest):
       try:
           domain_status = await platform.add_custom_domain(
               tenant_id, request.domain
           )
           return domain_status
       except TenantNotFoundError:
           raise HTTPException(status_code=404, detail="Tenant not found")

   @app.get("/domains/{domain}")
   async def get_domain_status(domain: str):
       status = await platform.get_custom_domain_status(domain)
       if not status:
           raise HTTPException(status_code=404, detail="Domain not found")
       return status

   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host="0.0.0.0", port=8000)

Logging Examples
----------------

Structured Logging
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel, LogFormat, get_logger

   # Configure JSON logging for production
   configure_logging(
       level=LogLevel.INFO,
       log_format=LogFormat.JSON,
       log_file="/var/log/cloudflare-saas.log"
   )

   logger = get_logger(__name__)

   async def process_deployment(tenant_id: str):
       logger.info(f"Starting deployment", extra={
           "tenant_id": tenant_id,
           "operation": "deployment"
       })
       
       try:
           # ... deployment logic ...
           logger.info("Deployment completed", extra={
               "tenant_id": tenant_id,
               "status": "success"
           })
       except Exception as e:
           logger.error("Deployment failed", extra={
               "tenant_id": tenant_id,
               "error": str(e),
               "status": "failed"
           })

Custom Logging Setup
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import LoggerMixin

   class CustomService(LoggerMixin):
       async def process_item(self, item_id: str):
           self.logger.debug(f"Processing item: {item_id}")
           
           try:
               # ... processing ...
               self.logger.info(f"Processed item: {item_id}")
               return True
           except Exception as e:
               self.logger.error(f"Failed to process {item_id}: {e}")
               raise

Testing Examples
----------------

Unit Tests
^^^^^^^^^^

.. code-block:: python

   import pytest
   from cloudflare_saas import (
       CloudflareSaaSPlatform,
       Config,
       InMemoryStorageAdapter,
   )

   @pytest.fixture
   async def platform():
       config = Config(
           cloudflare_api_token="test-token",
           cloudflare_account_id="test-account",
           cloudflare_zone_id="test-zone",
           r2_access_key_id="test-key",
           r2_secret_access_key="test-secret",
           r2_bucket_name="test-bucket",
           platform_domain="test.example.com",
           log_level="DEBUG",
       )
       
       storage = InMemoryStorageAdapter()
       return CloudflareSaaSPlatform(config, storage=storage)

   @pytest.mark.asyncio
   async def test_create_tenant(platform):
       tenant = await platform.create_tenant("Test", "test")
       
       assert tenant.tenant_id == "tenant-test"
       assert tenant.name == "Test"
       assert tenant.slug == "test"

   @pytest.mark.asyncio
   async def test_get_tenant(platform):
       created = await platform.create_tenant("Test", "test")
       retrieved = await platform.get_tenant(created.tenant_id)
       
       assert created.tenant_id == retrieved.tenant_id

See Also
--------

- :doc:`getting_started` - Getting started guide
- :doc:`api_reference` - Complete API reference
- :doc:`deployment` - Deployment guide

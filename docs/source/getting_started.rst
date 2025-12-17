Getting Started
===============

This guide will help you get started with the Cloudflare SaaS Platform library.

Installation
------------

Basic Installation
^^^^^^^^^^^^^^^^^^

Install the core library:

.. code-block:: bash

   pip install cloudflare aiodns aioboto3 pydantic python-terraform httpx tenacity

For development with PostgreSQL storage:

.. code-block:: bash

   pip install asyncpg

For web framework integration:

.. code-block:: bash

   pip install fastapi uvicorn[standard]

From Source
^^^^^^^^^^^

Clone and install from the repository:

.. code-block:: bash

   git clone https://github.com/yourusername/cloudflare-saas.git
   cd cloudflare-saas
   pip install -e ".[dev,web]"

Prerequisites
-------------

Before using the library, you'll need:

1. **Cloudflare Account**: Sign up at `cloudflare.com <https://cloudflare.com>`_
2. **API Token**: Create an API token with the following permissions:
   
   - Zone: Read
   - Zone: Edit
   - Account: R2 Read & Write
   - SSL and Certificates: Edit

3. **R2 Bucket**: Create an R2 bucket in your Cloudflare account
4. **Custom Hostname Zone**: Set up a zone for custom hostnames (for SaaS features)

Configuration
-------------

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

Create a ``.env`` file with the required credentials:

.. code-block:: bash

   # Required
   CLOUDFLARE_API_TOKEN=your-api-token
   CLOUDFLARE_ACCOUNT_ID=your-account-id
   CLOUDFLARE_ZONE_ID=your-zone-id
   R2_ACCESS_KEY_ID=your-r2-key-id
   R2_SECRET_ACCESS_KEY=your-r2-secret
   R2_BUCKET_NAME=yourplatform-sites
   PLATFORM_DOMAIN=yourplatform.com

   # Optional - Logging
   LOG_LEVEL=INFO
   LOG_FORMAT=detailed
   LOG_FILE=/var/log/cloudflare-saas.log
   ENABLE_CONSOLE_LOGGING=true

   # Optional - Other
   WORKER_SCRIPT_NAME=site-router
   INTERNAL_API_KEY=your-internal-key

Programmatic Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also configure the platform programmatically:

.. code-block:: python

   from cloudflare_saas import Config

   config = Config(
       cloudflare_api_token="your-token",
       cloudflare_account_id="your-account",
       cloudflare_zone_id="your-zone",
       r2_access_key_id="your-r2-key",
       r2_secret_access_key="your-r2-secret",
       r2_bucket_name="yourplatform-sites",
       platform_domain="yourplatform.com",
       log_level="DEBUG",
       log_format="json",
       log_file="app.log"
   )

Basic Usage
-----------

Initialize the Platform
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from cloudflare_saas import CloudflareSaaSPlatform, Config, configure_logging, LogLevel

   async def main():
       # Configure logging first
       configure_logging(level=LogLevel.INFO)
       
       # Load config from environment
       config = Config.from_env()
       
       # Initialize platform
       platform = CloudflareSaaSPlatform(config)

   if __name__ == "__main__":
       asyncio.run(main())

Create a Tenant
^^^^^^^^^^^^^^^

.. code-block:: python

   # Create tenant
   tenant = await platform.create_tenant(
       name="Acme Inc",
       slug="acme",
       owner_id="user-123",
       metadata={"plan": "premium"}
   )
   
   print(f"Created tenant: {tenant.tenant_id}")
   print(f"Subdomain: {tenant.subdomain}")

Deploy a Site
^^^^^^^^^^^^^

.. code-block:: python

   # Deploy static site files
   result = await platform.deploy_tenant_site(
       tenant_id=tenant.tenant_id,
       local_path="./acme-website"
   )
   
   if result.success:
       print(f"Deployed {result.files_uploaded} files")
       print(f"Total size: {result.total_size_bytes} bytes")
       print(f"Deployment time: {result.deployment_time_seconds}s")
   else:
       print(f"Deployment failed: {result.error_message}")

Add Custom Domain
^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Add custom domain for tenant
   domain_status = await platform.add_custom_domain(
       tenant_id=tenant.tenant_id,
       domain="www.acme.com"
   )
   
   print(f"Domain status: {domain_status.status}")
   print(f"SSL status: {domain_status.ssl_status}")
   
   # Get verification instructions
   instructions = await platform.get_domain_verification_instructions("www.acme.com")
   print(f"Verification type: {instructions.verification_method}")
   print(f"Instructions: {instructions.instructions}")

Next Steps
----------

- Learn about :doc:`configuration` options
- Explore :doc:`logging` capabilities
- Check out :doc:`examples` for more use cases
- Read the complete :doc:`api_reference`

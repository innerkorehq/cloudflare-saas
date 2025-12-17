Cloudflare SaaS Platform Documentation
======================================

Welcome to the Cloudflare SaaS Platform documentation! This library provides a production-ready Python async framework for building multi-tenant SaaS platforms using Cloudflare R2, Workers, and Custom Hostnames.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   configuration
   logging
   api_reference
   examples
   deployment
   contributing

Overview
--------

The Cloudflare SaaS Platform library enables you to:

* ✅ Manage async R2 bucket operations (upload, delete, list)
* ✅ Handle tenant management with namespace isolation
* ✅ Onboard custom domains with DNS verification
* ✅ Provision Cloudflare for SaaS custom hostnames
* ✅ Automate Worker deployment via Terraform
* ✅ Implement comprehensive error handling and retry logic
* ✅ Utilize type-safe Pydantic models

Key Features
------------

Multi-Tenant Architecture
^^^^^^^^^^^^^^^^^^^^^^^^^

The platform provides complete tenant isolation with:

- Namespace-based R2 storage separation
- Custom subdomain provisioning
- Custom domain support with SSL
- Pluggable storage backends (in-memory, PostgreSQL)

Cloudflare Integration
^^^^^^^^^^^^^^^^^^^^^^^

Seamless integration with Cloudflare services:

- **R2 Storage**: Object storage for tenant sites
- **Custom Hostnames**: Automated SSL provisioning
- **Workers**: Dynamic routing and request handling
- **DNS Management**: Automatic verification and setup

Production Ready
^^^^^^^^^^^^^^^^

Built for production use with:

- Comprehensive logging system
- Retry logic with exponential backoff
- Type safety with Pydantic
- Async/await throughout
- Extensive error handling

Quick Start
-----------

.. code-block:: bash

   pip install cloudflare-saas

.. code-block:: python

   import asyncio
   from cloudflare_saas import CloudflareSaaSPlatform, Config, configure_logging, LogLevel

   async def main():
       # Configure logging
       configure_logging(level=LogLevel.INFO)
       
       # Load configuration
       config = Config.from_env()
       
       # Initialize platform
       platform = CloudflareSaaSPlatform(config)
       
       # Create tenant
       tenant = await platform.create_tenant("Acme Inc", "acme")
       
       # Deploy site
       await platform.deploy_tenant_site(
           tenant.tenant_id,
           "./acme-site"
       )
       
       # Add custom domain
       domain_status = await platform.add_custom_domain(
           tenant.tenant_id,
           "www.acme.com"
       )

   asyncio.run(main())

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

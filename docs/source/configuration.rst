Configuration
=============

The Cloudflare SaaS Platform library offers extensive configuration options for customizing behavior, credentials, and logging.

Configuration Class
-------------------

The :class:`cloudflare_saas.Config` class manages all platform configuration.

.. autoclass:: cloudflare_saas.Config
   :members:
   :undoc-members:

Configuration Options
---------------------

Cloudflare Credentials
^^^^^^^^^^^^^^^^^^^^^^^

Required credentials for Cloudflare API access:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Option
     - Type
     - Description
   * - cloudflare_api_token
     - str
     - Cloudflare API token with required permissions
   * - cloudflare_account_id
     - str
     - Your Cloudflare account ID
   * - cloudflare_zone_id
     - str
     - Zone ID for custom hostname management

R2 Storage Credentials
^^^^^^^^^^^^^^^^^^^^^^^

Configuration for Cloudflare R2 object storage:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Option
     - Type
     - Description
   * - r2_access_key_id
     - str
     - R2 access key ID
   * - r2_secret_access_key
     - str
     - R2 secret access key
   * - r2_bucket_name
     - str
     - Name of the R2 bucket for tenant sites
   * - r2_endpoint
     - str (optional)
     - Custom R2 endpoint URL (auto-generated if not provided)

Platform Configuration
^^^^^^^^^^^^^^^^^^^^^^

Core platform settings:

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Option
     - Type
     - Default
     - Description
   * - platform_domain
     - str
     - (required)
     - Your platform's base domain for subdomains
   * - worker_script_name
     - str
     - "site-router"
     - Name of the Cloudflare Worker script
   * - internal_api_key
     - str
     - None
     - Optional API key for internal operations
   * - enable_custom_hostnames
     - bool
     - True
     - Enable/disable custom hostname functionality
   * - default_cache_ttl
     - int
     - 604800
     - Default cache TTL in seconds (7 days)

Logging Configuration
^^^^^^^^^^^^^^^^^^^^^

Control logging behavior:

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 45

   * - Option
     - Type
     - Default
     - Description
   * - log_level
     - str
     - "INFO"
     - Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   * - log_format
     - str
     - "detailed"
     - Log format (simple, detailed, json)
   * - log_file
     - str
     - None
     - Optional file path for log output
   * - enable_console_logging
     - bool
     - True
     - Enable/disable console output

Loading Configuration
---------------------

From Environment Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The recommended approach for production:

.. code-block:: python

   from cloudflare_saas import Config

   config = Config.from_env()

Environment variable mapping:

.. code-block:: bash

   # Required
   CLOUDFLARE_API_TOKEN=...
   CLOUDFLARE_ACCOUNT_ID=...
   CLOUDFLARE_ZONE_ID=...
   R2_ACCESS_KEY_ID=...
   R2_SECRET_ACCESS_KEY=...
   R2_BUCKET_NAME=...
   PLATFORM_DOMAIN=...

   # Optional
   WORKER_SCRIPT_NAME=...
   INTERNAL_API_KEY=...
   R2_ENDPOINT=...
   LOG_LEVEL=...
   LOG_FORMAT=...
   LOG_FILE=...
   ENABLE_CONSOLE_LOGGING=...

From Dictionary
^^^^^^^^^^^^^^^

Programmatic configuration:

.. code-block:: python

   from cloudflare_saas import Config

   config = Config(
       cloudflare_api_token="token",
       cloudflare_account_id="account",
       cloudflare_zone_id="zone",
       r2_access_key_id="key",
       r2_secret_access_key="secret",
       r2_bucket_name="bucket",
       platform_domain="example.com",
       log_level="DEBUG",
       log_format="json"
   )

From .env File
^^^^^^^^^^^^^^

Using python-dotenv:

.. code-block:: python

   from dotenv import load_dotenv
   from cloudflare_saas import Config

   load_dotenv()
   config = Config.from_env()

Configuration Examples
----------------------

Development Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import Config, LogLevel

   config = Config(
       # ... credentials ...
       log_level="DEBUG",
       log_format="detailed",
       enable_console_logging=True,
       log_file="dev.log"
   )

Production Configuration
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import Config

   config = Config(
       # ... credentials ...
       log_level="WARNING",
       log_format="json",
       enable_console_logging=False,
       log_file="/var/log/cloudflare-saas/app.log"
   )

Testing Configuration
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import Config, InMemoryStorageAdapter

   config = Config(
       # ... test credentials ...
       log_level="DEBUG",
       enable_custom_hostnames=False,  # Disable for faster tests
   )

Validation
----------

The Config class uses Pydantic for validation:

.. code-block:: python

   from cloudflare_saas import Config
   from pydantic import ValidationError

   try:
       config = Config(
           cloudflare_api_token="invalid",
           # Missing required fields
       )
   except ValidationError as e:
       print(e.errors())

Best Practices
--------------

1. **Use Environment Variables**: Store sensitive credentials in environment variables, not in code
2. **Separate Configurations**: Use different configs for dev, staging, and production
3. **Enable Logging**: Always configure logging appropriate to your environment
4. **Validate Early**: Load and validate configuration at application startup
5. **Secure Credentials**: Never commit credentials to version control
6. **Use .env Files**: Keep .env files out of version control with .gitignore

See Also
--------

- :doc:`logging` - Detailed logging configuration
- :doc:`getting_started` - Quick start guide
- :doc:`api_reference` - Complete API reference

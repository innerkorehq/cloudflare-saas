Logging
=======

The Cloudflare SaaS Platform library includes a comprehensive, configurable logging system to help you monitor operations, debug issues, and track platform activity.

Overview
--------

The logging system provides:

* **Multiple log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
* **Flexible formats**: Simple, detailed, and JSON formats
* **Console and file output**: Log to stdout and/or files
* **Rotating file handlers**: Automatic log rotation with size limits
* **Per-module loggers**: Fine-grained control over logging
* **Third-party library control**: Manage verbosity of dependencies

Quick Start
-----------

Basic Configuration
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel, LogFormat

   # Configure logging at application startup
   configure_logging(
       level=LogLevel.INFO,
       log_format=LogFormat.DETAILED
   )

With File Output
^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel, LogFormat

   configure_logging(
       level=LogLevel.DEBUG,
       log_format=LogFormat.JSON,
       log_file="cloudflare-saas.log",
       enable_console=True
   )

Log Levels
----------

The library supports standard Python logging levels:

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Level
     - Numeric
     - Use Case
   * - DEBUG
     - 10
     - Detailed information for diagnosing problems
   * - INFO
     - 20
     - General informational messages about operations
   * - WARNING
     - 30
     - Warning messages for potentially harmful situations
   * - ERROR
     - 40
     - Error events that might still allow operation
   * - CRITICAL
     - 50
     - Serious errors indicating system failure

Example Usage
^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import LogLevel, configure_logging

   # Development
   configure_logging(level=LogLevel.DEBUG)

   # Production
   configure_logging(level=LogLevel.WARNING)

   # Critical issues only
   configure_logging(level=LogLevel.CRITICAL)

Log Formats
-----------

Three built-in formats are available:

Simple Format
^^^^^^^^^^^^^

Minimal output for development:

.. code-block:: text

   INFO: Creating tenant: name=Acme Inc, slug=acme
   WARNING: Deployment path does not exist: /invalid/path

.. code-block:: python

   from cloudflare_saas import LogFormat, configure_logging

   configure_logging(log_format=LogFormat.SIMPLE)

Detailed Format
^^^^^^^^^^^^^^^

Comprehensive information with timestamps and source location:

.. code-block:: text

   2025-12-17 10:30:45 - CloudflareSaaSPlatform - INFO - [platform.py:65] - Creating tenant: name=Acme Inc, slug=acme
   2025-12-17 10:30:46 - R2Client - DEBUG - [r2_client.py:45] - Uploading file: /path/to/file

.. code-block:: python

   configure_logging(log_format=LogFormat.DETAILED)

JSON Format
^^^^^^^^^^^

Structured logging for production systems and log aggregators:

.. code-block:: json

   {"time": "2025-12-17 10:30:45", "name": "CloudflareSaaSPlatform", "level": "INFO", "file": "platform.py", "line": 65, "message": "Creating tenant: name=Acme Inc, slug=acme"}

.. code-block:: python

   configure_logging(log_format=LogFormat.JSON)

File Logging
------------

Rotating File Handler
^^^^^^^^^^^^^^^^^^^^^^

Logs automatically rotate when they reach 10MB:

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel

   configure_logging(
       level=LogLevel.INFO,
       log_file="/var/log/cloudflare-saas/app.log",
       enable_console=False
   )

This creates:
- ``app.log`` (current log)
- ``app.log.1`` (first backup)
- ``app.log.2`` (second backup)
- ... up to ``app.log.5`` (fifth backup)

Console and File Together
^^^^^^^^^^^^^^^^^^^^^^^^^^

Log to both console and file:

.. code-block:: python

   configure_logging(
       level=LogLevel.INFO,
       log_file="app.log",
       enable_console=True
   )

Using Loggers
-------------

Getting a Logger
^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import get_logger

   logger = get_logger(__name__)
   
   logger.debug("Debug message")
   logger.info("Info message")
   logger.warning("Warning message")
   logger.error("Error message")
   logger.critical("Critical message")

Logger Mixin
^^^^^^^^^^^^

For classes, use the LoggerMixin:

.. code-block:: python

   from cloudflare_saas import LoggerMixin

   class MyService(LoggerMixin):
       def do_work(self):
           self.logger.info("Starting work")
           try:
               # ... work ...
               self.logger.info("Work completed successfully")
           except Exception as e:
               self.logger.error(f"Work failed: {e}")
               raise

Configuration Reference
-----------------------

configure_logging()
^^^^^^^^^^^^^^^^^^^

.. autofunction:: cloudflare_saas.configure_logging

get_logger()
^^^^^^^^^^^^

.. autofunction:: cloudflare_saas.get_logger

LogLevel
^^^^^^^^

.. autoclass:: cloudflare_saas.LogLevel
   :members:
   :undoc-members:

LogFormat
^^^^^^^^^

.. autoclass:: cloudflare_saas.LogFormat
   :members:
   :undoc-members:

LoggerMixin
^^^^^^^^^^^

.. autoclass:: cloudflare_saas.LoggerMixin
   :members:

Examples
--------

Development Setup
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel, LogFormat

   configure_logging(
       level=LogLevel.DEBUG,
       log_format=LogFormat.DETAILED,
       enable_console=True
   )

Production Setup
^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import configure_logging, LogLevel, LogFormat

   configure_logging(
       level=LogLevel.WARNING,
       log_format=LogFormat.JSON,
       log_file="/var/log/cloudflare-saas/production.log",
       enable_console=False
   )

Docker/Container Setup
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import os
   from cloudflare_saas import configure_logging, LogLevel, LogFormat

   configure_logging(
       level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
       log_format=LogFormat.JSON,  # JSON for log aggregation
       enable_console=True,  # Log to stdout for container logs
       log_file=None  # Don't use file in containers
   )

Custom Logger Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from cloudflare_saas import get_logger

   # Get logger for specific module
   logger = get_logger("my_module")
   
   # Use throughout your code
   logger.info("Starting operation")
   logger.debug(f"Processing {count} items")
   logger.error(f"Failed to process item {item_id}")

Integration with Config
-----------------------

The Config class includes logging options:

.. code-block:: python

   from cloudflare_saas import Config, CloudflareSaaSPlatform

   config = Config(
       # ... other config ...
       log_level="DEBUG",
       log_format="json",
       log_file="app.log",
       enable_console_logging=True
   )
   
   # Platform automatically configures logging
   platform = CloudflareSaaSPlatform(config)

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # .env file
   LOG_LEVEL=DEBUG
   LOG_FORMAT=json
   LOG_FILE=/var/log/cloudflare-saas.log
   ENABLE_CONSOLE_LOGGING=true

.. code-block:: python

   from cloudflare_saas import Config, CloudflareSaaSPlatform

   config = Config.from_env()
   platform = CloudflareSaaSPlatform(config)  # Logging auto-configured

Third-Party Library Logging
----------------------------

The logging configuration automatically manages verbosity of dependencies:

* **httpx**: Set to WARNING (reduces HTTP request logging noise)
* **httpcore**: Set to WARNING
* **aioboto3**: Set to WARNING

You can override these by accessing the logger directly:

.. code-block:: python

   import logging
   
   # Enable debug logging for httpx
   logging.getLogger("httpx").setLevel(logging.DEBUG)

Best Practices
--------------

1. **Configure Early**: Set up logging at application startup
2. **Use Appropriate Levels**: DEBUG for development, WARNING/ERROR for production
3. **Structured Logging**: Use JSON format for production log aggregation
4. **Context in Messages**: Include relevant details in log messages
5. **Avoid Secrets**: Never log sensitive information (tokens, passwords, etc.)
6. **File Rotation**: Let the system handle log rotation automatically
7. **Container Logging**: Use console output (stdout) in containers

Troubleshooting
---------------

Logs Not Appearing
^^^^^^^^^^^^^^^^^^

Check that:

1. Logging is configured before other imports
2. Log level is not too restrictive
3. Console output is enabled if expecting stdout
4. File path is writable

Too Verbose
^^^^^^^^^^^

Reduce log level:

.. code-block:: python

   configure_logging(level=LogLevel.WARNING)

Or disable console output:

.. code-block:: python

   configure_logging(enable_console=False)

See Also
--------

- :doc:`configuration` - Configuration options
- :doc:`getting_started` - Getting started guide
- :doc:`api_reference` - API reference

API Reference
=============

Complete API reference for the Cloudflare SaaS Platform library.

Core Classes
------------

CloudflareSaaSPlatform
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.CloudflareSaaSPlatform
   :members:
   :undoc-members:
   :show-inheritance:

Config
^^^^^^

.. autoclass:: cloudflare_saas.Config
   :members:
   :undoc-members:
   :show-inheritance:

Clients
-------

CloudflareClient
^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.CloudflareClient
   :members:
   :undoc-members:
   :show-inheritance:

R2Client
^^^^^^^^

.. autoclass:: cloudflare_saas.R2Client
   :members:
   :undoc-members:
   :show-inheritance:

DNSVerifier
^^^^^^^^^^^

.. autoclass:: cloudflare_saas.DNSVerifier
   :members:
   :undoc-members:
   :show-inheritance:

TerraformDeployer
^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.TerraformDeployer
   :members:
   :undoc-members:
   :show-inheritance:

Storage Adapters
----------------

StorageAdapter
^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.StorageAdapter
   :members:
   :undoc-members:
   :show-inheritance:

InMemoryStorageAdapter
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.InMemoryStorageAdapter
   :members:
   :undoc-members:
   :show-inheritance:

PostgresStorageAdapter
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.PostgresStorageAdapter
   :members:
   :undoc-members:
   :show-inheritance:

Data Models
-----------

Tenant
^^^^^^

.. autoclass:: cloudflare_saas.Tenant
   :members:
   :undoc-members:
   :show-inheritance:

CustomDomain
^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.CustomDomain
   :members:
   :undoc-members:
   :show-inheritance:

DomainStatus
^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.DomainStatus
   :members:
   :undoc-members:
   :show-inheritance:

DeploymentResult
^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.DeploymentResult
   :members:
   :undoc-members:
   :show-inheritance:

VerificationMethod
^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.VerificationMethod
   :members:
   :undoc-members:
   :show-inheritance:

HostnameVerificationInstructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.HostnameVerificationInstructions
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

CloudflareSaaSException
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.CloudflareSaaSException
   :members:
   :undoc-members:
   :show-inheritance:

TenantNotFoundError
^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.TenantNotFoundError
   :members:
   :undoc-members:
   :show-inheritance:

DomainVerificationError
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.DomainVerificationError
   :members:
   :undoc-members:
   :show-inheritance:

DeploymentError
^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.DeploymentError
   :members:
   :undoc-members:
   :show-inheritance:

R2OperationError
^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.R2OperationError
   :members:
   :undoc-members:
   :show-inheritance:

CustomHostnameError
^^^^^^^^^^^^^^^^^^^

.. autoclass:: cloudflare_saas.CustomHostnameError
   :members:
   :undoc-members:
   :show-inheritance:

DNSError
^^^^^^^^

.. autoclass:: cloudflare_saas.DNSError
   :members:
   :undoc-members:
   :show-inheritance:

Logging
-------

configure_logging
^^^^^^^^^^^^^^^^^

.. autofunction:: cloudflare_saas.configure_logging

get_logger
^^^^^^^^^^

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
   :undoc-members:

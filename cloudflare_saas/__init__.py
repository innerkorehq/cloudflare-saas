"""
Cloudflare R2 SaaS Platform Library

A production-ready async library for multi-tenant SaaS platforms.
"""

from .platform import CloudflareSaaSPlatform
from .config import Config
from .logging_config import (
    configure_logging,
    get_logger,
    LogLevel,
    LogFormat,
    LoggerMixin,
)
from .models import (
    Tenant,
    CustomDomain,
    DomainStatus,
    DeploymentResult,
    VerificationMethod,
    HostnameVerificationInstructions,
)
from .exceptions import (
    CloudflareSaaSException,
    TenantNotFoundError,
    DomainVerificationError,
    DeploymentError,
    R2OperationError,
    CustomHostnameError,
    DNSError,
)
from .storage_adapter import StorageAdapter, InMemoryStorageAdapter
from .postgres_adapter import PostgresStorageAdapter
from .r2_client import R2Client
from .cloudflare_client import CloudflareClient
from .dns_verifier import DNSVerifier
from .terraform_deployer import TerraformDeployer

__version__ = "1.0.0"

__all__ = [
    "CloudflareSaaSPlatform",
    "Config",
    "configure_logging",
    "get_logger",
    "LogLevel",
    "LogFormat",
    "LoggerMixin",
    "Tenant",
    "CustomDomain",
    "DomainStatus",
    "DeploymentResult",
    "VerificationMethod",
    "HostnameVerificationInstructions",
    "CloudflareSaaSException",
    "TenantNotFoundError",
    "DomainVerificationError",
    "DeploymentError",
    "R2OperationError",
    "CustomHostnameError",
    "DNSError",
    "StorageAdapter",
    "InMemoryStorageAdapter",
    "PostgresStorageAdapter",
    "R2Client",
    "CloudflareClient",
    "DNSVerifier",
    "TerraformDeployer",
]
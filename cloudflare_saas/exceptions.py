"""Custom exceptions for Cloudflare SaaS library."""


class CloudflareSaaSException(Exception):
    """Base exception for all Cloudflare SaaS operations."""
    pass


class TenantNotFoundError(CloudflareSaaSException):
    """Raised when tenant is not found."""
    pass


class DomainVerificationError(CloudflareSaaSException):
    """Raised when domain verification fails."""
    pass


class DeploymentError(CloudflareSaaSException):
    """Raised when site deployment fails."""
    pass


class R2OperationError(CloudflareSaaSException):
    """Raised when R2 operations fail."""
    pass


class CustomHostnameError(CloudflareSaaSException):
    """Raised when custom hostname operations fail."""
    pass


class DNSError(CloudflareSaaSException):
    """Raised when DNS operations fail."""
    pass
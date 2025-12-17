"""Pydantic models for type safety."""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class DomainStatus(str, Enum):
    """Status of custom domain provisioning."""
    PENDING = "pending"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    ACTIVE = "active"
    FAILED = "failed"


class VerificationMethod(str, Enum):
    """DNS verification method."""
    HTTP = "http"
    TXT = "txt"
    EMAIL = "email"


class Tenant(BaseModel):
    """Tenant model."""
    tenant_id: str
    name: str
    slug: str
    subdomain: str
    owner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('tenant_id', pre=True, always=True)
    def set_tenant_id(cls, v, values):
        if not v and 'slug' in values:
            return f"tenant-{values['slug']}"
        return v

    @validator('subdomain', pre=True, always=True)
    def set_subdomain(cls, v, values):
        if not v and 'tenant_id' in values:
            # Will be set after tenant_id is computed
            return None
        return v


class CustomDomain(BaseModel):
    """Custom domain model."""
    domain: str
    tenant_id: str
    status: DomainStatus = DomainStatus.PENDING
    verification_method: VerificationMethod = VerificationMethod.HTTP
    verification_token: Optional[str] = None
    cname_target: Optional[str] = None
    cloudflare_hostname_id: Optional[str] = None
    ssl_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verified_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DeploymentResult(BaseModel):
    """Result of site deployment."""
    tenant_id: str
    files_uploaded: int
    total_size_bytes: int
    deployment_time_seconds: float
    success: bool
    error_message: Optional[str] = None
    uploaded_paths: List[str] = Field(default_factory=list)


class HostnameVerificationInstructions(BaseModel):
    """Instructions for domain verification."""
    domain: str
    cname_target: str
    verification_method: VerificationMethod
    http_verification_url: Optional[str] = None
    http_verification_token: Optional[str] = None
    txt_record_name: Optional[str] = None
    txt_record_value: Optional[str] = None
    instructions: str
"""Tests for CloudflareSaaS platform."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from cloudflare_saas import (
    CloudflareSaaSPlatform,
    Config,
    InMemoryStorageAdapter,
    Tenant,
    DomainStatus,
    VerificationMethod,
)
from cloudflare_saas.exceptions import TenantNotFoundError, DomainVerificationError


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        cloudflare_api_token="test-token",
        cloudflare_account_id="test-account",
        cloudflare_zone_id="test-zone",
        r2_access_key_id="test-key",
        r2_secret_access_key="test-secret",
        r2_bucket_name="test-bucket",
        platform_domain="testplatform.com",
        enable_custom_hostnames=False,  # Disable for testing
    )


@pytest.fixture
def storage():
    """Create test storage adapter."""
    return InMemoryStorageAdapter()


@pytest.fixture
def platform(config, storage):
    """Create test platform instance."""
    return CloudflareSaaSPlatform(config, storage)


@pytest.mark.asyncio
async def test_create_tenant(platform):
    """Test tenant creation."""
    tenant = await platform.create_tenant(
        name="Test Company",
        slug="test-co",
        owner_id="owner-123",
    )
    
    assert tenant.tenant_id == "tenant-test-co"
    assert tenant.name == "Test Company"
    assert tenant.subdomain == "tenant-test-co.testplatform.com"
    assert tenant.owner_id == "owner-123"


@pytest.mark.asyncio
async def test_get_tenant(platform):
    """Test tenant retrieval."""
    created = await platform.create_tenant("Test", "test", "owner-1")
    
    retrieved = await platform.get_tenant(created.tenant_id)
    
    assert retrieved.tenant_id == created.tenant_id
    assert retrieved.name == created.name


@pytest.mark.asyncio
async def test_get_nonexistent_tenant(platform):
    """Test retrieving non-existent tenant raises error."""
    with pytest.raises(TenantNotFoundError):
        await platform.get_tenant("nonexistent")


@pytest.mark.asyncio
async def test_list_tenants(platform):
    """Test tenant listing."""
    await platform.create_tenant("Tenant 1", "tenant-1")
    await platform.create_tenant("Tenant 2", "tenant-2")
    await platform.create_tenant("Tenant 3", "tenant-3")
    
    tenants = await platform.list_tenants(limit=2)
    
    assert len(tenants) == 2


@pytest.mark.asyncio
async def test_resolve_tenant_from_subdomain(platform):
    """Test resolving tenant from subdomain."""
    tenant = await platform.create_tenant("Test", "test")
    
    resolved = await platform.resolve_tenant_from_host("tenant-test.testplatform.com")
    
    assert resolved == tenant.tenant_id


@pytest.mark.asyncio
async def test_add_custom_domain(platform):
    """Test adding custom domain."""
    tenant = await platform.create_tenant("Test", "test")
    
    instructions = await platform.add_custom_domain(
        tenant.tenant_id,
        "www.example.com",
        VerificationMethod.HTTP,
    )
    
    assert instructions.domain == "www.example.com"
    assert instructions.cname_target == tenant.subdomain
    assert instructions.http_verification_token is not None


@pytest.mark.asyncio
async def test_add_duplicate_domain_same_tenant(platform):
    """Test adding same domain twice to same tenant."""
    tenant = await platform.create_tenant("Test", "test")
    
    await platform.add_custom_domain(tenant.tenant_id, "www.example.com")
    
    # Should not raise error
    await platform.add_custom_domain(tenant.tenant_id, "www.example.com")


@pytest.mark.asyncio
async def test_add_duplicate_domain_different_tenant(platform):
    """Test adding domain that belongs to another tenant."""
    tenant1 = await platform.create_tenant("Tenant 1", "tenant-1")
    tenant2 = await platform.create_tenant("Tenant 2", "tenant-2")
    
    await platform.add_custom_domain(tenant1.tenant_id, "www.example.com")
    
    with pytest.raises(DomainVerificationError):
        await platform.add_custom_domain(tenant2.tenant_id, "www.example.com")


@pytest.mark.asyncio
async def test_get_domain_status(platform):
    """Test getting domain status."""
    tenant = await platform.create_tenant("Test", "test")
    await platform.add_custom_domain(tenant.tenant_id, "www.example.com")
    
    status = await platform.get_domain_status("www.example.com")
    
    assert status.domain == "www.example.com"
    assert status.tenant_id == tenant.tenant_id
    assert status.status in [DomainStatus.PENDING, DomainStatus.VERIFYING]


@pytest.mark.asyncio
async def test_list_tenant_domains(platform):
    """Test listing tenant domains."""
    tenant = await platform.create_tenant("Test", "test")
    
    await platform.add_custom_domain(tenant.tenant_id, "www.example1.com")
    await platform.add_custom_domain(tenant.tenant_id, "www.example2.com")
    
    domains = await platform.list_tenant_domains(tenant.tenant_id)
    
    assert len(domains) == 2
    assert all(d.tenant_id == tenant.tenant_id for d in domains)


@pytest.mark.asyncio
async def test_remove_custom_domain(platform):
    """Test removing custom domain."""
    tenant = await platform.create_tenant("Test", "test")
    await platform.add_custom_domain(tenant.tenant_id, "www.example.com")
    
    await platform.remove_custom_domain("www.example.com")
    
    with pytest.raises(DomainVerificationError):
        await platform.get_domain_status("www.example.com")


@pytest.mark.asyncio
async def test_delete_tenant(platform):
    """Test tenant deletion."""
    tenant = await platform.create_tenant("Test", "test")
    
    # Mock R2 delete
    with patch.object(platform.r2, 'delete_tenant_objects', return_value=0):
        await platform.delete_tenant(tenant.tenant_id)
    
    with pytest.raises(TenantNotFoundError):
        await platform.get_tenant(tenant.tenant_id)


@pytest.mark.asyncio
async def test_delete_tenant_with_domains(platform):
    """Test tenant deletion cascades to domains."""
    tenant = await platform.create_tenant("Test", "test")
    await platform.add_custom_domain(tenant.tenant_id, "www.example.com")
    
    with patch.object(platform.r2, 'delete_tenant_objects', return_value=0):
        await platform.delete_tenant(tenant.tenant_id)
    
    # Domain should be deleted
    with pytest.raises(DomainVerificationError):
        await platform.get_domain_status("www.example.com")
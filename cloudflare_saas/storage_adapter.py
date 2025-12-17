"""Storage adapter interface for persistence layer."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime

from .models import Tenant, CustomDomain


class StorageAdapter(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    async def save_tenant(self, tenant: Tenant) -> None:
        """Save tenant to storage."""
        pass
    
    @abstractmethod
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieve tenant by ID."""
        pass
    
    @abstractmethod
    async def delete_tenant(self, tenant_id: str) -> None:
        """Delete tenant from storage."""
        pass
    
    @abstractmethod
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        """List all tenants with pagination."""
        pass
    
    @abstractmethod
    async def save_domain(self, domain: CustomDomain) -> None:
        """Save custom domain to storage."""
        pass
    
    @abstractmethod
    async def get_domain(self, domain: str) -> Optional[CustomDomain]:
        """Retrieve custom domain by hostname."""
        pass
    
    @abstractmethod
    async def delete_domain(self, domain: str) -> None:
        """Delete custom domain from storage."""
        pass
    
    @abstractmethod
    async def list_tenant_domains(self, tenant_id: str) -> List[CustomDomain]:
        """List all domains for a tenant."""
        pass
    
    @abstractmethod
    async def get_domain_by_tenant(self, domain: str) -> Optional[str]:
        """Get tenant ID for active domain."""
        pass


class InMemoryStorageAdapter(StorageAdapter):
    """In-memory storage implementation (for testing/development)."""
    
    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._domains: Dict[str, CustomDomain] = {}
        self._tenant_domains: Dict[str, List[str]] = {}
    
    async def save_tenant(self, tenant: Tenant) -> None:
        self._tenants[tenant.tenant_id] = tenant
        if tenant.tenant_id not in self._tenant_domains:
            self._tenant_domains[tenant.tenant_id] = []
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)
    
    async def delete_tenant(self, tenant_id: str) -> None:
        self._tenants.pop(tenant_id, None)
        self._tenant_domains.pop(tenant_id, None)
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        tenants = list(self._tenants.values())
        return tenants[offset:offset + limit]
    
    async def save_domain(self, domain: CustomDomain) -> None:
        self._domains[domain.domain] = domain
        tenant_id = domain.tenant_id
        if tenant_id not in self._tenant_domains:
            self._tenant_domains[tenant_id] = []
        if domain.domain not in self._tenant_domains[tenant_id]:
            self._tenant_domains[tenant_id].append(domain.domain)
    
    async def get_domain(self, domain: str) -> Optional[CustomDomain]:
        return self._domains.get(domain)
    
    async def delete_domain(self, domain: str) -> None:
        domain_obj = self._domains.pop(domain, None)
        if domain_obj:
            tenant_domains = self._tenant_domains.get(domain_obj.tenant_id, [])
            if domain in tenant_domains:
                tenant_domains.remove(domain)
    
    async def list_tenant_domains(self, tenant_id: str) -> List[CustomDomain]:
        domain_names = self._tenant_domains.get(tenant_id, [])
        return [self._domains[d] for d in domain_names if d in self._domains]
    
    async def get_domain_by_tenant(self, domain: str) -> Optional[str]:
        domain_obj = self._domains.get(domain)
        if domain_obj and domain_obj.status.value == "active":
            return domain_obj.tenant_id
        return None
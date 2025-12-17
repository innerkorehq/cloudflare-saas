"""Platform orchestrator with pluggable storage."""

import asyncio
import secrets
import time
from pathlib import Path
from typing import Optional, List, Dict

from .config import Config
from .logging_config import LoggerMixin, configure_logging, LogLevel, LogFormat
from .models import (
    Tenant,
    CustomDomain,
    DomainStatus,
    DeploymentResult,
    VerificationMethod,
    HostnameVerificationInstructions,
)
from .r2_client import R2Client
from .cloudflare_client import CloudflareClient
from .dns_verifier import DNSVerifier
from .storage_adapter import StorageAdapter, InMemoryStorageAdapter
from .exceptions import (
    TenantNotFoundError,
    DeploymentError,
    DomainVerificationError,
)


class CloudflareSaaSPlatform(LoggerMixin):
    """
    Main platform orchestrator with pluggable storage.
    
    This class coordinates R2 storage, Cloudflare custom hostnames,
    DNS verification, and tenant management with configurable persistence.
    """
    
    def __init__(
        self,
        config: Config,
        storage: Optional[StorageAdapter] = None,
    ):
        self.config = config
        self.r2 = R2Client(config)
        self.cloudflare = CloudflareClient(config)
        self.dns = DNSVerifier()
        
        # Use provided storage or default to in-memory
        self.storage = storage or InMemoryStorageAdapter()
        
        # Configure logging based on config
        configure_logging(
            level=LogLevel(config.log_level),
            log_format=LogFormat(config.log_format),
            log_file=config.log_file,
            enable_console=config.enable_console_logging,
        )
        
        self.logger.info(
            f"Initialized CloudflareSaaSPlatform for domain: {config.platform_domain}"
        )
    
    # ==================== Tenant Management ====================
    
    async def create_tenant(
        self,
        name: str,
        slug: str,
        owner_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Tenant:
        """Create a new tenant."""
        self.logger.info(f"Creating tenant: name={name}, slug={slug}")
        
        tenant_id = f"tenant-{slug}"
        subdomain = f"{tenant_id}.{self.config.platform_domain}"
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            subdomain=subdomain,
            owner_id=owner_id,
            metadata=metadata or {},
        )
        
        await self.storage.save_tenant(tenant)
        self.logger.info(f"Successfully created tenant: {tenant_id}")
        return tenant
    
    async def get_tenant(self, tenant_id: str) -> Tenant:
        """Get tenant by ID."""
        self.logger.debug(f"Fetching tenant: {tenant_id}")
        tenant = await self.storage.get_tenant(tenant_id)
        if not tenant:
            self.logger.error(f"Tenant not found: {tenant_id}")
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        self.logger.debug(f"Found tenant: {tenant_id}")
        return tenant
    
    async def list_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        """List tenants with pagination."""
        return await self.storage.list_tenants(limit, offset)
    
    async def delete_tenant(self, tenant_id: str) -> None:
        """Delete tenant and all associated resources."""
        self.logger.warning(f"Deleting tenant and all resources: {tenant_id}")
        await self.get_tenant(tenant_id)
        
        # Delete R2 objects
        self.logger.info(f"Deleting R2 objects for tenant: {tenant_id}")
        await self.r2.delete_tenant_objects(tenant_id)
        
        # Delete custom domains
        domains = await self.storage.list_tenant_domains(tenant_id)
        self.logger.info(f"Deleting {len(domains)} custom domains for tenant: {tenant_id}")
        for domain in domains:
            try:
                await self.remove_custom_domain(domain.domain)
            except Exception as e:
                self.logger.error(f"Failed to remove domain {domain.domain}: {e}")
                pass  # Continue cleanup
        
        await self.storage.delete_tenant(tenant_id)
        self.logger.info(f"Successfully deleted tenant: {tenant_id}")
    
    async def resolve_tenant_from_host(self, host: str) -> Optional[str]:
        """Resolve tenant ID from hostname."""
        # Fast path: subdomain
        if host.endswith(f".{self.config.platform_domain}"):
            tenant_id = host.replace(f".{self.config.platform_domain}", "")
            tenant = await self.storage.get_tenant(tenant_id)
            if tenant:
                return tenant_id
        
        # Slow path: custom domain lookup
        return await self.storage.get_domain_by_tenant(host)
    
    # ==================== Site Deployment ====================
    
    async def deploy_tenant_site(
        self,
        tenant_id: str,
        local_path: str,
        base_prefix: str = "",
    ) -> DeploymentResult:
        """Deploy static site for tenant."""
        self.logger.info(f"Starting deployment for tenant: {tenant_id}, path: {local_path}")
        await self.get_tenant(tenant_id)
        
        local_dir = Path(local_path)
        if not local_dir.exists():
            self.logger.error(f"Deployment path does not exist: {local_path}")
            raise DeploymentError(f"Path {local_path} does not exist")
        
        start_time = time.time()
        
        try:
            uploaded_keys = await self.r2.upload_directory(
                tenant_id,
                local_dir,
                base_prefix,
            )
            
            total_size = sum(
                f.stat().st_size
                for f in local_dir.rglob('*')
                if f.is_file()
            )
            
            deployment_time = time.time() - start_time
            
            self.logger.info(
                f"Deployment successful for {tenant_id}: "
                f"{len(uploaded_keys)} files, {total_size} bytes, {deployment_time:.2f}s"
            )
            
            return DeploymentResult(
                tenant_id=tenant_id,
                files_uploaded=len(uploaded_keys),
                total_size_bytes=total_size,
                deployment_time_seconds=deployment_time,
                success=True,
                uploaded_paths=uploaded_keys,
            )
        except Exception as e:
            self.logger.error(f"Deployment failed for {tenant_id}: {e}")
            return DeploymentResult(
                tenant_id=tenant_id,
                files_uploaded=0,
                total_size_bytes=0,
                deployment_time_seconds=time.time() - start_time,
                success=False,
                error_message=str(e),
            )
    
    async def get_deployment_status(self, tenant_id: str) -> Dict:
        """Get deployment status for tenant."""
        await self.get_tenant(tenant_id)
        
        objects = await self.r2.list_tenant_objects(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "object_count": len(objects),
            "total_size_bytes": sum(obj.get('Size', 0) for obj in objects),
            "objects": objects,
        }
    
    # ==================== Custom Domain Management ====================
    
    async def add_custom_domain(
        self,
        tenant_id: str,
        domain: str,
        verification_method: VerificationMethod = VerificationMethod.HTTP,
    ) -> HostnameVerificationInstructions:
        """Start custom domain onboarding process."""
        tenant = await self.get_tenant(tenant_id)
        
        existing = await self.storage.get_domain(domain)
        if existing:
            if existing.tenant_id != tenant_id:
                raise DomainVerificationError(
                    f"Domain {domain} is already registered to another tenant"
                )
        
        verification_token = secrets.token_urlsafe(32)
        cname_target = tenant.subdomain
        
        custom_domain = CustomDomain(
            domain=domain,
            tenant_id=tenant_id,
            status=DomainStatus.PENDING,
            verification_method=verification_method,
            verification_token=verification_token,
            cname_target=cname_target,
        )
        
        await self.storage.save_domain(custom_domain)
        
        # Start async verification
        asyncio.create_task(self._verify_and_provision_domain(domain))
        
        instructions = f"""
To activate your custom domain '{domain}', please:

1. Add a CNAME record:
   - Name: {domain}
   - Value: {cname_target}

2. The SSL certificate will be automatically provisioned once DNS is verified.

3. Verification typically takes 5-10 minutes after DNS propagation.
"""
        
        result = HostnameVerificationInstructions(
            domain=domain,
            cname_target=cname_target,
            verification_method=verification_method,
            instructions=instructions,
        )
        
        if verification_method == VerificationMethod.HTTP:
            result.http_verification_url = f"http://{domain}/.well-known/cf-custom-hostname-challenge/{verification_token}"
            result.http_verification_token = verification_token
        elif verification_method == VerificationMethod.TXT:
            result.txt_record_name = f"_cf-custom-hostname.{domain}"
            result.txt_record_value = verification_token
        
        return result
    
    async def _verify_and_provision_domain(self, domain: str) -> None:
        """Background task to verify DNS and provision custom hostname."""
        custom_domain = await self.storage.get_domain(domain)
        if not custom_domain:
            return
        
        try:
            custom_domain.status = DomainStatus.VERIFYING
            await self.storage.save_domain(custom_domain)
            
            cname_verified = await self.dns.wait_for_cname(
                domain,
                custom_domain.cname_target,
                max_attempts=30,
                delay_seconds=10,
            )
            
            if not cname_verified:
                custom_domain.status = DomainStatus.FAILED
                custom_domain.error_message = "CNAME verification timed out"
                await self.storage.save_domain(custom_domain)
                return
            
            custom_domain.status = DomainStatus.VERIFIED
            await self.storage.save_domain(custom_domain)
            
            if self.config.enable_custom_hostnames:
                cf_result = await self.cloudflare.create_custom_hostname(
                    domain,
                    custom_domain.verification_method,
                )
                
                custom_domain.cloudflare_hostname_id = cf_result["id"]
                custom_domain.ssl_status = cf_result["ssl_status"]
                custom_domain.status = DomainStatus.ACTIVE
            else:
                custom_domain.status = DomainStatus.ACTIVE
            
            await self.storage.save_domain(custom_domain)
            
        except Exception as e:
            custom_domain.status = DomainStatus.FAILED
            custom_domain.error_message = str(e)
            await self.storage.save_domain(custom_domain)
    
    async def get_domain_status(self, domain: str) -> CustomDomain:
        """Get status of custom domain provisioning."""
        custom_domain = await self.storage.get_domain(domain)
        if not custom_domain:
            raise DomainVerificationError(f"Domain {domain} not found")
        
        if custom_domain.cloudflare_hostname_id:
            try:
                cf_status = await self.cloudflare.get_custom_hostname(
                    custom_domain.cloudflare_hostname_id
                )
                custom_domain.ssl_status = cf_status["ssl_status"]
                if cf_status["status"] == "active":
                    custom_domain.status = DomainStatus.ACTIVE
                await self.storage.save_domain(custom_domain)
            except Exception:
                pass
        
        return custom_domain
    
    async def remove_custom_domain(self, domain: str) -> None:
        """Remove custom domain."""
        custom_domain = await self.storage.get_domain(domain)
        if not custom_domain:
            raise DomainVerificationError(f"Domain {domain} not found")
        
        if custom_domain.cloudflare_hostname_id:
            try:
                await self.cloudflare.delete_custom_hostname(
                    custom_domain.cloudflare_hostname_id
                )
            except Exception:
                pass
        
        await self.storage.delete_domain(domain)
    
    async def list_tenant_domains(self, tenant_id: str) -> List[CustomDomain]:
        """List all domains for a tenant."""
        await self.get_tenant(tenant_id)
        return await self.storage.list_tenant_domains(tenant_id)
"""Cloudflare API client for custom hostnames."""

from typing import Optional, Dict, Any

from cloudflare import AsyncCloudflare
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from .config import Config
from .models import VerificationMethod
from .exceptions import CustomHostnameError
from .logging_config import LoggerMixin


class CloudflareClient(LoggerMixin):
    """Async Cloudflare API client."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncCloudflare(api_token=config.cloudflare_api_token)
        self.logger.info(f"Initialized CloudflareClient for zone: {config.cloudflare_zone_id}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def create_custom_hostname(
        self,
        hostname: str,
        verification_method: VerificationMethod = VerificationMethod.HTTP,
    ) -> Dict[str, Any]:
        """Create custom hostname in Cloudflare for SaaS."""
        self.logger.info(f"Creating custom hostname: {hostname} with method: {verification_method.value}")
        try:
            response = await self.client.custom_hostnames.create(
                zone_id=self.config.cloudflare_zone_id,
                hostname=hostname,
                ssl={
                    "method": verification_method.value,
                    "type": "dv",
                    "settings": {
                        "http2": "on",
                        "min_tls_version": "1.2",
                        "tls_1_3": "on",
                    }
                },
            )
            
            self.logger.info(f"Successfully created custom hostname: {hostname}, id: {response.id}")
            
            # Attach custom hostname to worker route
            try:
                await self._attach_hostname_to_worker(hostname)
                self.logger.info(f"Attached custom hostname {hostname} to worker {self.config.worker_script_name}")
            except Exception as route_error:
                self.logger.warning(f"Failed to attach worker route for {hostname}: {route_error}")
                # Don't fail the whole operation if route creation fails
            
            return {
                "id": response.id,
                "hostname": response.hostname,
                "status": response.status,
                "verification_errors": response.verification_errors,
                "ssl_status": response.ssl.status if response.ssl else None,
                "ssl_validation_records": response.ssl.validation_records if response.ssl else None,
                "ownership_verification": response.ownership_verification,
                "ownership_verification_http": response.ownership_verification_http,
            }
        except Exception as e:
            self.logger.error(f"Failed to create custom hostname {hostname}: {e}")
            raise CustomHostnameError(f"Failed to create custom hostname: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def get_custom_hostname(
        self,
        hostname_id: str,
    ) -> Dict[str, Any]:
        """Get custom hostname status."""
        try:
            response = await self.client.custom_hostnames.get(
                custom_hostname_id=hostname_id,
                zone_id=self.config.cloudflare_zone_id,
            )
            
            return {
                "id": response.id,
                "hostname": response.hostname,
                "status": response.status,
                "ssl_status": response.ssl.status if response.ssl else None,
                "verification_errors": response.verification_errors,
            }
        except Exception as e:
            raise CustomHostnameError(f"Failed to get custom hostname: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def delete_custom_hostname(
        self,
        hostname_id: str,
        hostname: Optional[str] = None,
    ) -> None:
        """Delete custom hostname."""
        try:
            # Get hostname if not provided
            if not hostname:
                hostname_info = await self.get_custom_hostname(hostname_id)
                hostname = hostname_info.get("hostname")
            
            # Detach worker route first (before deleting the hostname)
            if hostname:
                try:
                    await self._detach_hostname_from_worker(hostname)
                    self.logger.info(f"Detached custom hostname {hostname} from worker")
                except Exception as route_error:
                    self.logger.warning(f"Failed to detach worker route for {hostname}: {route_error}")
                    # Continue with deletion even if route removal fails
            
            # Delete the custom hostname
            await self.client.custom_hostnames.delete(
                custom_hostname_id=hostname_id,
                zone_id=self.config.cloudflare_zone_id,
            )
            self.logger.info(f"Successfully deleted custom hostname: {hostname_id}")
        except Exception as e:
            raise CustomHostnameError(f"Failed to delete custom hostname: {e}")
    
    async def list_custom_hostnames(
        self,
        hostname: Optional[str] = None,
    ) -> list:
        """List custom hostnames."""
        try:
            params = {}
            if hostname:
                params["hostname"] = hostname
            
            response = await self.client.custom_hostnames.list(
                zone_id=self.config.cloudflare_zone_id,
                **params
            )
            
            return [
                {
                    "id": item.id,
                    "hostname": item.hostname,
                    "status": item.status,
                    "ssl_status": item.ssl.status if item.ssl else None,
                }
                for item in response.result
            ]
        except Exception as e:
            raise CustomHostnameError(f"Failed to list custom hostnames: {e}")
    
    async def _attach_hostname_to_worker(self, hostname: str) -> Dict[str, Any]:
        """Attach custom hostname to worker route."""
        pattern = f"{hostname}/*"
        
        try:
            response = await self.client.workers.routes.create(
                zone_id=self.config.cloudflare_zone_id,
                pattern=pattern,
                script=self.config.worker_script_name,
            )
            
            self.logger.info(f"Created worker route: {pattern} -> {self.config.worker_script_name}")
            return {
                "id": response.id,
                "pattern": pattern,
                "script": self.config.worker_script_name,
            }
        except Exception as e:
            self.logger.error(f"Failed to create worker route for {hostname}: {e}")
            raise
    
    async def _detach_hostname_from_worker(self, hostname: str) -> None:
        """Detach custom hostname from worker route."""
        pattern = f"{hostname}/*"
        
        try:
            # List all routes and find the matching one
            routes_page = await self.client.workers.routes.list(
                zone_id=self.config.cloudflare_zone_id,
            )
            
            # Iterate through async iterator
            async for route in routes_page:
                # Route objects have direct attributes
                if hasattr(route, 'pattern') and route.pattern == pattern:
                    route_id = route.id
                    await self.client.workers.routes.delete(
                        route_id=route_id,
                        zone_id=self.config.cloudflare_zone_id,
                    )
                    self.logger.info(f"Deleted worker route: {pattern}")
                    return
            
            self.logger.warning(f"Worker route not found for pattern: {pattern}")
        except Exception as e:
            self.logger.error(f"Failed to delete worker route for {hostname}: {e}")
            raise
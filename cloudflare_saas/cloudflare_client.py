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
    ) -> None:
        """Delete custom hostname."""
        try:
            await self.client.custom_hostnames.delete(
                custom_hostname_id=hostname_id,
                zone_id=self.config.cloudflare_zone_id,
            )
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
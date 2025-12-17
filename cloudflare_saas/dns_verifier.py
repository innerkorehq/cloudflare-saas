"""DNS verification utilities using aiodns."""

import asyncio
from typing import List, Optional

import aiodns
from aiodns.error import DNSError as AIODNSError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .exceptions import DNSError


class DNSVerifier:
    """Async DNS verification."""
    
    def __init__(self):
        self.resolver = aiodns.DNSResolver()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(AIODNSError),
    )
    async def verify_cname(
        self,
        domain: str,
        expected_target: str,
    ) -> bool:
        """Verify CNAME record points to expected target."""
        try:
            result = await self.resolver.query(domain, 'CNAME')
            
            # Normalize targets (remove trailing dots)
            actual_targets = [r.host.rstrip('.') for r in result]
            expected = expected_target.rstrip('.')
            
            return expected in actual_targets
        except AIODNSError as e:
            # No CNAME record found
            if 'NXDOMAIN' in str(e) or 'No answer' in str(e):
                return False
            raise DNSError(f"DNS query failed for {domain}: {e}")
        except Exception as e:
            raise DNSError(f"Unexpected DNS error: {e}")
    
    async def get_cname_records(self, domain: str) -> List[str]:
        """Get all CNAME records for a domain."""
        try:
            result = await self.resolver.query(domain, 'CNAME')
            return [r.host.rstrip('.') for r in result]
        except AIODNSError:
            return []
        except Exception as e:
            raise DNSError(f"Failed to get CNAME records: {e}")
    
    async def verify_txt(
        self,
        domain: str,
        expected_value: str,
    ) -> bool:
        """Verify TXT record contains expected value."""
        try:
            result = await self.resolver.query(domain, 'TXT')
            
            actual_values = [r.text.decode('utf-8') if isinstance(r.text, bytes) else r.text for r in result]
            
            return expected_value in actual_values
        except AIODNSError:
            return False
        except Exception as e:
            raise DNSError(f"Failed to verify TXT record: {e}")
    
    async def wait_for_cname(
        self,
        domain: str,
        expected_target: str,
        max_attempts: int = 30,
        delay_seconds: int = 10,
    ) -> bool:
        """Poll for CNAME verification with retries."""
        for attempt in range(max_attempts):
            try:
                if await self.verify_cname(domain, expected_target):
                    return True
            except DNSError:
                pass
            
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay_seconds)
        
        return False
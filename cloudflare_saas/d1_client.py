"""Cloudflare D1 Database client."""

import httpx
from typing import Optional, Dict, Any, List
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from .config import Config
from .exceptions import CloudflareSaaSException
from .logging_config import LoggerMixin


class D1Client(LoggerMixin):
    """Async Cloudflare D1 Database client."""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{config.cloudflare_account_id}/d1/database"
        self.headers = {
            "Authorization": f"Bearer {config.cloudflare_api_token}",
            "Content-Type": "application/json",
        }
        self.logger.info(f"Initialized D1Client for database: {config.d1_database_id}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def execute_query(
        self,
        sql: str,
        params: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a SQL query on D1 database."""
        if not self.config.d1_database_id:
            raise CloudflareSaaSException("D1 database ID not configured")
        
        url = f"{self.base_url}/{self.config.d1_database_id}/query"
        
        payload = {
            "sql": sql,
            "params": params or []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                error_msg = f"D1 query failed: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                raise CloudflareSaaSException(error_msg)
            
            result = response.json()
            if not result.get("success"):
                error_msg = f"D1 query error: {result.get('errors', [])}"
                self.logger.error(error_msg)
                raise CloudflareSaaSException(error_msg)
            
            return result
    
    async def insert_domain(
        self,
        name: str,
        zone: str,
        tenant_id: str,
    ) -> bool:
        """Insert or update a domain record."""
        sql = """
        INSERT OR REPLACE INTO domains (name, zone, tenant_id, last_date)
        VALUES (?, ?, ?, datetime('now'))
        """
        
        try:
            result = await self.execute_query(sql, [name, zone, tenant_id])
            self.logger.info(f"Inserted/updated domain: {name} -> {tenant_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to insert domain {name}: {e}")
            return False
    
    async def update_domain_tenant(
        self,
        name: str,
        zone: str,
        tenant_id: str,
    ) -> bool:
        """Update tenant_id for a domain."""
        sql = """
        UPDATE domains 
        SET tenant_id = ?, updated = datetime('now'), last_date = datetime('now')
        WHERE name = ? AND zone = ?
        """
        
        try:
            result = await self.execute_query(sql, [tenant_id, name, zone])
            self.logger.info(f"Updated domain tenant: {name} -> {tenant_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update domain {name}: {e}")
            return False
    
    async def delete_domain(
        self,
        name: str,
        zone: str,
    ) -> bool:
        """Delete a domain record."""
        sql = """
        DELETE FROM domains 
        WHERE name = ? AND zone = ?
        """
        
        try:
            result = await self.execute_query(sql, [name, zone])
            self.logger.info(f"Deleted domain: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete domain {name}: {e}")
            return False
    
    async def get_domain(
        self,
        name: str,
        zone: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a domain record."""
        sql = """
        SELECT name, zone, tenant_id, created, updated, last_date
        FROM domains 
        WHERE name = ? AND zone = ?
        """
        
        try:
            result = await self.execute_query(sql, [name, zone])
            rows = result.get("result", [])
            if rows and len(rows) > 0 and len(rows[0].get("results", [])) > 0:
                return rows[0]["results"][0]
            return None
        except Exception as e:
            self.logger.error(f"Failed to get domain {name}: {e}")
            return None
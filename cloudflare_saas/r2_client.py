"""R2 client for bucket operations using aioboto3."""

import asyncio
import os
import mimetypes
from pathlib import Path
from typing import List, Optional, AsyncIterator
from contextlib import asynccontextmanager

import aioboto3
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .exceptions import R2OperationError
from .config import Config
from .logging_config import LoggerMixin


class R2Client(LoggerMixin):
    """Async R2 client for object operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = aioboto3.Session(
            aws_access_key_id=config.r2_access_key_id,
            aws_secret_access_key=config.r2_secret_access_key,
        )
        self.logger.info(f"Initialized R2Client for bucket: {config.r2_bucket_name}")
    
    @asynccontextmanager
    async def _get_client(self):
        """Get S3 client context manager."""
        async with self.session.client(
            's3',
            endpoint_url=self.config.r2_endpoint,
            region_name='auto',
        ) as client:
            yield client
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def upload_file(
        self,
        tenant_id: str,
        local_path: Path,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload a file to R2 under tenant namespace."""
        if content_type is None:
            content_type, _ = mimetypes.guess_type(str(local_path))
            if content_type is None:
                content_type = 'application/octet-stream'
        
        # Construct namespaced key
        namespaced_key = f"{tenant_id}/{object_key}"
        
        try:
            async with self._get_client() as client:
                with open(local_path, 'rb') as f:
                    await client.put_object(
                        Bucket=self.config.r2_bucket_name,
                        Key=namespaced_key,
                        Body=f,
                        ContentType=content_type,
                    )
            return namespaced_key
        except ClientError as e:
            raise R2OperationError(
                f"Failed to upload {local_path} to {namespaced_key}: {e}"
            )
        except Exception as e:
            raise R2OperationError(f"Unexpected error uploading file: {e}")
    
    async def upload_directory(
        self,
        tenant_id: str,
        local_dir: Path,
        base_prefix: str = "",
    ) -> List[str]:
        """Upload entire directory to R2."""
        if not local_dir.is_dir():
            raise R2OperationError(f"{local_dir} is not a directory")
        
        uploaded_keys = []
        tasks = []
        
        for file_path in local_dir.rglob('*'):
            if file_path.is_file():
                # Calculate relative path
                rel_path = file_path.relative_to(local_dir)
                object_key = str(rel_path).replace('\\', '/')
                
                if base_prefix:
                    object_key = f"{base_prefix}/{object_key}"
                
                # Create upload task
                task = self.upload_file(tenant_id, file_path, object_key)
                tasks.append(task)
        
        # Upload files concurrently
        try:
            uploaded_keys = await asyncio.gather(*tasks)
        except Exception as e:
            raise R2OperationError(f"Failed to upload directory: {e}")
        
        return uploaded_keys
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
    )
    async def delete_object(self, tenant_id: str, object_key: str) -> None:
        """Delete an object from R2."""
        namespaced_key = f"{tenant_id}/{object_key}"
        
        try:
            async with self._get_client() as client:
                await client.delete_object(
                    Bucket=self.config.r2_bucket_name,
                    Key=namespaced_key,
                )
        except ClientError as e:
            raise R2OperationError(f"Failed to delete {namespaced_key}: {e}")
    
    async def delete_tenant_objects(self, tenant_id: str) -> int:
        """Delete all objects for a tenant."""
        keys_to_delete = []
        
        try:
            async with self._get_client() as client:
                # List all objects with tenant prefix
                paginator = client.get_paginator('list_objects_v2')
                async for page in paginator.paginate(
                    Bucket=self.config.r2_bucket_name,
                    Prefix=f"{tenant_id}/",
                ):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            keys_to_delete.append({'Key': obj['Key']})
                
                # Delete in batches of 1000 (S3 limit)
                deleted_count = 0
                for i in range(0, len(keys_to_delete), 1000):
                    batch = keys_to_delete[i:i+1000]
                    await client.delete_objects(
                        Bucket=self.config.r2_bucket_name,
                        Delete={'Objects': batch},
                    )
                    deleted_count += len(batch)
                
                return deleted_count
        except ClientError as e:
            raise R2OperationError(f"Failed to delete tenant objects: {e}")
    
    async def list_tenant_objects(
        self,
        tenant_id: str,
        max_keys: int = 1000,
    ) -> List[dict]:
        """List objects for a tenant."""
        objects = []
        
        try:
            async with self._get_client() as client:
                response = await client.list_objects_v2(
                    Bucket=self.config.r2_bucket_name,
                    Prefix=f"{tenant_id}/",
                    MaxKeys=max_keys,
                )
                
                if 'Contents' in response:
                    objects = response['Contents']
                
                return objects
        except ClientError as e:
            raise R2OperationError(f"Failed to list tenant objects: {e}")
    
    async def object_exists(self, tenant_id: str, object_key: str) -> bool:
        """Check if object exists."""
        namespaced_key = f"{tenant_id}/{object_key}"
        
        try:
            async with self._get_client() as client:
                await client.head_object(
                    Bucket=self.config.r2_bucket_name,
                    Key=namespaced_key,
                )
                return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise R2OperationError(f"Failed to check object existence: {e}")
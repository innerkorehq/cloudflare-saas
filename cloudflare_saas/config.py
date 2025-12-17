"""Configuration management."""

import os
from typing import Optional
from pydantic import BaseModel, validator


class Config(BaseModel):
    """Configuration for Cloudflare SaaS platform."""
    
    # Cloudflare credentials
    cloudflare_api_token: str
    cloudflare_account_id: str
    cloudflare_zone_id: str
    
    # R2 credentials
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    r2_endpoint: Optional[str] = None
    
    # Platform configuration
    platform_domain: str
    worker_script_name: str = "site-router"
    internal_api_key: Optional[str] = None
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "detailed"
    log_file: Optional[str] = None
    enable_console_logging: bool = True
    
    # Optional features
    enable_custom_hostnames: bool = True
    default_cache_ttl: int = 604800  # 7 days
    
    @validator('r2_endpoint', pre=True, always=True)
    def set_r2_endpoint(cls, v, values):
        if not v and 'cloudflare_account_id' in values:
            account_id = values['cloudflare_account_id']
            return f"https://{account_id}.r2.cloudflarestorage.com"
        return v
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        required_vars = {
            'CLOUDFLARE_API_TOKEN': 'cloudflare_api_token',
            'CLOUDFLARE_ACCOUNT_ID': 'cloudflare_account_id',
            'CLOUDFLARE_ZONE_ID': 'cloudflare_zone_id',
            'R2_ACCESS_KEY_ID': 'r2_access_key_id',
            'R2_SECRET_ACCESS_KEY': 'r2_secret_access_key',
            'R2_BUCKET_NAME': 'r2_bucket_name',
            'PLATFORM_DOMAIN': 'platform_domain',
        }
        
        missing = [k for k in required_vars if not os.getenv(k)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please set the following environment variables:\n" +
                "\n".join(f"  - {k}" for k in missing)
            )
        
        config_dict = {
            v: os.getenv(k) for k, v in required_vars.items()
        }
        
        # Optional variables
        optional_vars = {
            'WORKER_SCRIPT_NAME': 'worker_script_name',
            'INTERNAL_API_KEY': 'internal_api_key',
            'R2_ENDPOINT': 'r2_endpoint',
            'LOG_LEVEL': 'log_level',
            'LOG_FORMAT': 'log_format',
            'LOG_FILE': 'log_file',
        }
        
        for env_key, config_key in optional_vars.items():
            val = os.getenv(env_key)
            if val:
                config_dict[config_key] = val
        
        # Boolean environment variables
        if os.getenv('ENABLE_CONSOLE_LOGGING'):
            config_dict['enable_console_logging'] = os.getenv('ENABLE_CONSOLE_LOGGING').lower() in ('true', '1', 'yes')
        
        return cls(**config_dict)

    class Config:
        validate_assignment = True
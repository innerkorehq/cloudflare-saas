# Cloudflare R2 SaaS Platform Library

A production-ready Python async library for building multi-tenant SaaS platforms with Cloudflare R2, Workers, and Custom Hostnames.

[![Documentation Status](https://readthedocs.org/projects/cloudflare-saas/badge/?version=latest)](https://cloudflare-saas.readthedocs.io/en/latest/?badge=latest)

## Features

- ✅ Async R2 bucket operations (upload, delete, list)
- ✅ Tenant management with namespace isolation
- ✅ Custom domain onboarding with DNS verification
- ✅ Cloudflare for SaaS custom hostname provisioning
- ✅ Worker deployment automation via Terraform
- ✅ **Configurable logging system** (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ **Multiple log formats** (simple, detailed, JSON)
- ✅ Full error handling and retry logic
- ✅ Type-safe with Pydantic models
- ✅ Comprehensive documentation

## Installation

```bash
pip install cloudflare aiodns aioboto3 pydantic python-terraform httpx tenacity
```

For PostgreSQL storage:

```bash
pip install asyncpg
```

For development:

```bash
pip install -e ".[dev,web]"
```

## Quick Start

### Basic Usage with Logging

```python
import asyncio
from cloudflare_saas import (
    CloudflareSaaSPlatform, 
    Config, 
    configure_logging, 
    LogLevel
)

async def main():
    # Configure logging
    configure_logging(level=LogLevel.INFO)
    
    # Load config from environment
    config = Config.from_env()
    
    # Initialize platform
    platform = CloudflareSaaSPlatform(config)
    
    # Create tenant
    tenant = await platform.create_tenant("Acme Inc", "acme-123")
    
    # Deploy site
    await platform.deploy_tenant_site(
        tenant.tenant_id,
        local_path="./acme-site"
    )
    
    # Add custom domain
    domain_status = await platform.add_custom_domain(
        tenant.tenant_id,
        "www.acme.com"
    )

asyncio.run(main())
```

## Configuration

### Environment Variables

Required:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_ZONE_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `PLATFORM_DOMAIN`

Optional - Logging:
- `LOG_LEVEL` (default: INFO) - DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_FORMAT` (default: detailed) - simple, detailed, json
- `LOG_FILE` - Path to log file (optional)
- `ENABLE_CONSOLE_LOGGING` (default: true) - Enable console output

### Programmatic Configuration

```python
from cloudflare_saas import Config

config = Config(
    cloudflare_api_token="your-token",
    cloudflare_account_id="your-account",
    cloudflare_zone_id="your-zone",
    r2_access_key_id="your-r2-key",
    r2_secret_access_key="your-r2-secret",
    r2_bucket_name="yourplatform-sites",
    platform_domain="yourplatform.com",
    log_level="DEBUG",
    log_format="json",
    log_file="app.log"
)
```

## Logging

### Configure Logging

```python
from cloudflare_saas import configure_logging, LogLevel, LogFormat

# Simple console logging
configure_logging(level=LogLevel.INFO)

# Detailed file logging
configure_logging(
    level=LogLevel.DEBUG,
    log_format=LogFormat.DETAILED,
    log_file="cloudflare-saas.log"
)

# JSON logging for production
configure_logging(
    level=LogLevel.WARNING,
    log_format=LogFormat.JSON,
    log_file="/var/log/cloudflare-saas.log",
    enable_console=False
)
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Log Formats

- **simple**: Minimal output `INFO: message`
- **detailed**: With timestamps and source `2025-12-17 10:30:45 - Module - INFO - [file.py:65] - message`
- **json**: Structured JSON for log aggregation

### Using Loggers in Your Code

```python
from cloudflare_saas import get_logger, LoggerMixin

# Get a logger
logger = get_logger(__name__)
logger.info("Starting operation")

# Use in a class
class MyService(LoggerMixin):
    def do_work(self):
        self.logger.info("Working...")
```

## Documentation

Comprehensive documentation is available at [Read the Docs](https://cloudflare-saas.readthedocs.io/).

### Build Documentation Locally

```bash
# Install documentation dependencies
make install-docs

# Build HTML documentation
make docs

# Serve documentation locally
make docs-serve
```

Documentation includes:

- **Getting Started Guide**: Quick start and installation
- **Configuration Guide**: All configuration options
- **Logging Guide**: Comprehensive logging documentation
- **API Reference**: Complete API documentation
- **Examples**: Practical code examples
- **Deployment Guide**: Production deployment
- **Contributing Guide**: Development guidelines

## Development

### Available Make Commands

```bash
make help          # Show all available commands

# Development
make install       # Install package
make install-dev   # Install with dev dependencies
make install-docs  # Install documentation dependencies

# Testing
make test          # Run tests
make test-cov      # Run tests with coverage
make test-watch    # Run tests in watch mode

# Code Quality
make lint          # Run linters (ruff, mypy)
make format        # Format code (black, ruff)
make check         # Run all checks (lint + test)

# Documentation
make docs          # Build documentation
make docs-serve    # Build and serve documentation
make docs-clean    # Clean documentation build

# Docker
make docker-build  # Build Docker image
make docker-run    # Run Docker container
make docker-stop   # Stop Docker containers

# API
make run-api       # Run FastAPI development server

# Utilities
make clean         # Clean build artifacts
make clean-all     # Clean all generated files
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
pytest tests/test_platform.py::test_create_tenant -v
```

### Code Quality

```bash
# Format code
make format

# Check linting
make lint

# Run all checks
make check
```

## Architecture

See [cloudflare_r2_plan.md](./cloudflare_r2_plan.md) for detailed architecture.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./docs/source/contributing.rst) for guidelines.

### Development Setup

1. Fork and clone the repository
2. Install development dependencies: `make install-dev`
3. Create a branch for your feature
4. Make your changes with tests
5. Run tests and linting: `make check`
6. Submit a pull request

## License

[Add your license here]

## Support

- **Documentation**: https://cloudflare-saas.readthedocs.io/
- **Issues**: https://github.com/yourusername/cloudflare-saas/issues
- **Discussions**: https://github.com/yourusername/cloudflare-saas/discussions
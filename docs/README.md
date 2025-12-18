# Documentation

This folder contains comprehensive documentation for the Cloudflare SaaS platform.

## Documentation Files

### Core Documentation

- **[COMPLETE_SYSTEM.md](COMPLETE_SYSTEM.md)** - Complete system overview, architecture, and operational guide
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details and decisions
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment procedures and infrastructure setup

### Deployment & Operations

- **[DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md)** - Successful deployment results and metrics
- **[WORKER_DEPLOYMENT.md](WORKER_DEPLOYMENT.md)** - Worker script deployment via API
- **[DNS_SETUP_GUIDE.md](DNS_SETUP_GUIDE.md)** - DNS configuration for getai.page domain

### Configuration & Setup

- **[PERMISSIONS_GUIDE.md](PERMISSIONS_GUIDE.md)** - API token types and required permissions
- **[TOKEN_CREATION_GUIDE.md](TOKEN_CREATION_GUIDE.md)** - Creating API tokens with proper permissions

### Project Management

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## Quick Access

### Getting Started
1. Read [COMPLETE_SYSTEM.md](COMPLETE_SYSTEM.md) for full system overview
2. Follow [DNS_SETUP_GUIDE.md](DNS_SETUP_GUIDE.md) for domain setup
3. Use [DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md) for deployment verification

### Troubleshooting
- API permissions: [PERMISSIONS_GUIDE.md](PERMISSIONS_GUIDE.md)
- Token creation: [TOKEN_CREATION_GUIDE.md](TOKEN_CREATION_GUIDE.md)
- Worker deployment: [WORKER_DEPLOYMENT.md](WORKER_DEPLOYMENT.md)

## Sphinx Documentation

The `source/` folder contains Sphinx documentation (RST files) for the library API reference.

To build the documentation:

```bash
cd docs
pip install -r requirements.txt
make html
```

## Contributing to Documentation

When adding new documentation:

1. Place markdown files in this `docs/` folder
2. Update this README.md to include the new file
3. Reference documentation files with relative paths from the docs folder
4. Keep the root directory clean - only README.md should be in the project root
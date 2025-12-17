# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-17

### Added

#### Logging System
- Comprehensive configurable logging system
- Multiple log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Three log formats: simple, detailed, and JSON
- File and console output with rotating file handlers
- `configure_logging()` function for easy setup
- `get_logger()` function for module-specific loggers
- `LoggerMixin` class for adding logging to custom classes
- Integration with Config for environment-based logging setup
- Automatic third-party library log level management (httpx, aioboto3, etc.)

#### Documentation
- Complete ReadTheDocs-compatible documentation
- Getting Started guide
- Configuration reference
- Comprehensive logging guide
- API reference with autodoc
- Examples and use cases
- Deployment guide
- Contributing guidelines
- Sphinx-based documentation with RTD theme
- Support for both RST and Markdown formats

#### Makefile Enhancements
- `make help` - Display all available commands
- `make install-docs` - Install documentation dependencies
- `make docs` - Build documentation
- `make docs-serve` - Build and serve documentation locally
- `make docs-clean` - Clean documentation build
- `make test-watch` - Run tests in watch mode
- `make check` - Run all checks (lint + test)
- `make docker-stop` - Stop Docker containers
- `make deploy-test` - Deploy to Test PyPI
- `make clean-all` - Clean all generated files
- Enhanced output with informative messages

#### Configuration
- Logging configuration options in Config class:
  - `log_level` - Set logging level
  - `log_format` - Choose log format
  - `log_file` - Optional file output
  - `enable_console_logging` - Toggle console output
- Environment variable support for all logging options
- Updated `.env.example` with logging configuration

### Changed
- Updated README.md with comprehensive documentation
- Enhanced platform classes with logging integration
- CloudflareSaaSPlatform, R2Client, CloudflareClient now extend LoggerMixin
- Improved error messages with contextual logging
- Updated __init__.py to export logging components

### Fixed
- Import error with CustomHostname from cloudflare package

## [0.1.0] - Initial Release

### Added
- Basic async R2 operations
- Tenant management
- Custom hostname provisioning
- DNS verification
- Worker deployment via Terraform
- Type-safe Pydantic models
- Error handling and retry logic

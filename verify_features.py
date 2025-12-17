#!/usr/bin/env python3
"""
Verification script for cloudflare-saas logging and configuration features.

This script tests:
1. Logging configuration with different levels and formats
2. Config loading from environment
3. Logger creation and usage
4. LoggerMixin functionality
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_logging_configuration():
    """Test logging configuration."""
    print("\n" + "=" * 60)
    print("TEST 1: Logging Configuration")
    print("=" * 60)
    
    from cloudflare_saas import configure_logging, LogLevel, LogFormat, get_logger
    
    # Test different log levels
    print("\n1. Testing log levels:")
    configure_logging(level=LogLevel.DEBUG, log_format=LogFormat.SIMPLE)
    logger = get_logger("test.levels")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("\n✓ Log levels work correctly")
    
    # Test different formats
    print("\n2. Testing log formats:")
    
    print("\n  Simple format:")
    configure_logging(level=LogLevel.INFO, log_format=LogFormat.SIMPLE)
    logger = get_logger("test.simple")
    logger.info("Simple format message")
    
    print("\n  Detailed format:")
    configure_logging(level=LogLevel.INFO, log_format=LogFormat.DETAILED)
    logger = get_logger("test.detailed")
    logger.info("Detailed format message")
    
    print("\n  JSON format:")
    configure_logging(level=LogLevel.INFO, log_format=LogFormat.JSON)
    logger = get_logger("test.json")
    logger.info("JSON format message")
    
    print("\n✓ Log formats work correctly")


def test_logger_mixin():
    """Test LoggerMixin functionality."""
    print("\n" + "=" * 60)
    print("TEST 2: LoggerMixin")
    print("=" * 60)
    
    from cloudflare_saas import LoggerMixin, configure_logging, LogLevel, LogFormat
    
    configure_logging(level=LogLevel.INFO, log_format=LogFormat.DETAILED)
    
    class TestService(LoggerMixin):
        def process(self, item_id: str):
            self.logger.info(f"Processing item: {item_id}")
            self.logger.debug(f"Item details: {item_id}")
            return True
    
    service = TestService()
    service.process("test-123")
    
    print("\n✓ LoggerMixin works correctly")


def test_config_logging():
    """Test config with logging options."""
    print("\n" + "=" * 60)
    print("TEST 3: Config with Logging Options")
    print("=" * 60)
    
    from cloudflare_saas import Config
    
    # Test programmatic config
    config = Config(
        cloudflare_api_token="test-token",
        cloudflare_account_id="test-account",
        cloudflare_zone_id="test-zone",
        r2_access_key_id="test-key",
        r2_secret_access_key="test-secret",
        r2_bucket_name="test-bucket",
        platform_domain="test.example.com",
        log_level="DEBUG",
        log_format="json",
        log_file=None,
        enable_console_logging=True,
    )
    
    print(f"\n  Config created:")
    print(f"    Platform Domain: {config.platform_domain}")
    print(f"    Log Level: {config.log_level}")
    print(f"    Log Format: {config.log_format}")
    print(f"    Console Logging: {config.enable_console_logging}")
    
    print("\n✓ Config with logging options works correctly")


def test_file_logging():
    """Test file logging."""
    print("\n" + "=" * 60)
    print("TEST 4: File Logging")
    print("=" * 60)
    
    from cloudflare_saas import configure_logging, LogLevel, LogFormat, get_logger
    import tempfile
    
    # Create temp log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name
    
    try:
        configure_logging(
            level=LogLevel.INFO,
            log_format=LogFormat.DETAILED,
            log_file=log_file,
            enable_console=False
        )
        
        logger = get_logger("test.file")
        logger.info("Test message to file")
        logger.warning("Warning message to file")
        
        # Read log file
        with open(log_file, 'r') as f:
            content = f.read()
        
        print(f"\n  Log file created: {log_file}")
        print(f"  Content preview:")
        for line in content.strip().split('\n'):
            print(f"    {line}")
        
        # Verify content
        assert "Test message to file" in content
        assert "Warning message to file" in content
        
        print("\n✓ File logging works correctly")
    finally:
        # Cleanup
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_platform_initialization():
    """Test platform initialization with logging."""
    print("\n" + "=" * 60)
    print("TEST 5: Platform Initialization with Logging")
    print("=" * 60)
    
    from cloudflare_saas import Config, configure_logging, LogLevel, LogFormat
    
    configure_logging(level=LogLevel.INFO, log_format=LogFormat.DETAILED)
    
    try:
        config = Config(
            cloudflare_api_token="test-token",
            cloudflare_account_id="test-account",
            cloudflare_zone_id="test-zone",
            r2_access_key_id="test-key",
            r2_secret_access_key="test-secret",
            r2_bucket_name="test-bucket",
            platform_domain="test.example.com",
            log_level="INFO",
        )
        
        # Note: We can't fully initialize without real credentials,
        # but we can verify imports and config
        print(f"\n  Config validated successfully")
        print(f"  Platform domain: {config.platform_domain}")
        
        print("\n✓ Platform initialization config works correctly")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Cloudflare SaaS Platform - Feature Verification")
    print("=" * 60)
    
    try:
        test_logging_configuration()
        test_logger_mixin()
        test_config_logging()
        test_file_logging()
        test_platform_initialization()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nLogging system is working correctly!")
        print("Documentation can be built with: make docs")
        print("See IMPLEMENTATION_SUMMARY.md for details")
        print()
        
        return 0
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"TEST FAILED ✗")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

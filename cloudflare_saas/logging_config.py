"""Logging configuration for cloudflare-saas."""

import logging
import logging.config
import sys
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log output formats."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"


LOGGING_FORMATS = {
    "simple": "%(levelname)s: %(message)s",
    "detailed": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    "json": '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "file": "%(filename)s", "line": %(lineno)d, "message": "%(message)s"}',
}


def configure_logging(
    level: LogLevel = LogLevel.INFO,
    log_format: LogFormat = LogFormat.DETAILED,
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: The format of log messages (simple, detailed, json)
        log_file: Optional file path to write logs to
        enable_console: Whether to enable console output
        
    Examples:
        >>> from cloudflare_saas.logging_config import configure_logging, LogLevel, LogFormat
        >>> configure_logging(level=LogLevel.DEBUG, log_format=LogFormat.JSON)
        >>> configure_logging(level=LogLevel.INFO, log_file="app.log")
    """
    handlers: Dict[str, Any] = {}
    handler_names = []
    
    # Console handler
    if enable_console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": level.value,
            "formatter": log_format.value,
            "stream": "ext://sys.stdout",
        }
        handler_names.append("console")
    
    # File handler
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level.value,
            "formatter": log_format.value,
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }
        handler_names.append("file")
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": LOGGING_FORMATS["simple"]},
            "detailed": {
                "format": LOGGING_FORMATS["detailed"],
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {"format": LOGGING_FORMATS["json"]},
        },
        "handlers": handlers,
        "loggers": {
            "cloudflare_saas": {
                "level": level.value,
                "handlers": handler_names,
                "propagate": False,
            },
            # Third-party library logging levels
            "httpx": {
                "level": "WARNING",
                "handlers": handler_names,
                "propagate": False,
            },
            "httpcore": {
                "level": "WARNING",
                "handlers": handler_names,
                "propagate": False,
            },
            "aioboto3": {
                "level": "WARNING",
                "handlers": handler_names,
                "propagate": False,
            },
        },
        "root": {
            "level": level.value,
            "handlers": handler_names,
        },
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: The name of the logger (typically __name__)
        
    Returns:
        A configured logger instance
        
    Examples:
        >>> from cloudflare_saas.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting operation")
    """
    return logging.getLogger(f"cloudflare_saas.{name}")


class LoggerMixin:
    """
    Mixin class to add logging capability to any class.
    
    Examples:
        >>> class MyService(LoggerMixin):
        ...     def do_work(self):
        ...         self.logger.info("Doing work")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

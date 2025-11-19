#!/usr/bin/env python3
"""
A custom logging utility that provides a centralized logging configuration that automatically prefixes
all log messages with a given string. It also includes special "beacon" logging for timing operations.
"""

import logging
import sys
import time
from logging.handlers import RotatingFileHandler

# Import Google Cloud Logging components conditionally to avoid eager initialization
# This ensures that `google.cloud.logging.Client()` is not called at module import time
# unless explicitly enabled later.
try:
    import google.cloud.logging
    from google.cloud.logging.handlers import CloudLoggingHandler

    _GOOGLE_CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    _GOOGLE_CLOUD_LOGGING_AVAILABLE = False
    print(
        "Warning: google-cloud-logging not installed. Google Cloud Logging functionality will be disabled.",
        file=sys.stderr,
    )
except Exception as e:
    _GOOGLE_CLOUD_LOGGING_AVAILABLE = False
    print(
        f"Warning: Failed to import google.cloud.logging: {e}. Google Cloud Logging functionality will be disabled."
    )


# Module-level flag to ensure logging setup runs only once
_logging_configured = False


class PrefixedLogger:
    """A logger wrapper that automatically prefixes messages with a given string."""

    def __init__(self, logger_name, prefix=None):
        self.logger = logging.getLogger(logger_name)
        self._prefix = prefix or "no-prefix"
        self._start_times = {}  # For beacon timers

    def _format_message(self, message):
        """Add prefix to the message."""
        return f"[{self._prefix}] {message}"

    def update_prefix(self, prefix):
        """Update the prefix for log messages."""
        self._prefix = prefix or "no-prefix"

    def info(self, message, *args, **kwargs):
        """Log an info message with prefix."""
        self.logger.info(self._format_message(message), *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """Log a debug message with prefix."""
        self.logger.debug(self._format_message(message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """Log a warning message with prefix."""
        self.logger.warning(self._format_message(message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """Log an error message with prefix."""
        self.logger.error(self._format_message(message), *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """Log a critical message with prefix."""
        self.logger.critical(self._format_message(message), *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        """Log an exception message with prefix."""
        self.logger.exception(self._format_message(message), *args, **kwargs)

    def log_beacon(self, key, message, *args, **kwargs):
        """
        Logs a BEEP beacon.
        Args:
            key: A unique string key to identify the operation.
            message: The log message.
        """
        beacon_message = f"(BEACON - [{key}] - BLIP) {message}"
        self.info(beacon_message, *args, **kwargs)

    def log_b(self, key, message, *args, **kwargs):
        return self.log_beacon(key, message, *args, **kwargs)

    def log_start(self, key, message, *args, **kwargs):
        """
        Logs a START beacon for a timed operation.
        Args:
            key: A unique string key to identify the operation.
            message: The log message.
        """
        self._start_times[key] = time.perf_counter()
        beacon_message = f"(BEACON - [{key}] - START) {message}"
        self.info(beacon_message, *args, **kwargs)

    def log_end(self, key, message, *args, **kwargs):
        """
        Logs an END beacon for a timed operation and reports the elapsed time.
        Args:
            key: The unique string key used in log_start.
            message: The log message.
        """
        start_time = self._start_times.pop(key, None)
        if start_time is None:
            self.warning(
                f"log_end called for key '{key}' without a corresponding log_start."
            )
            beacon_message = f"(BEACON - [{key}] - END (Elapsed time N/A s)) {message}"
        else:
            elapsed_time = time.perf_counter() - start_time
            beacon_message = f"(BEACON - [{key}] - END (Elapsed time {elapsed_time:.2f} s)) {message}"
        self.info(beacon_message, *args, **kwargs)


def setup_logging(
    logger_name="chronotag",
    cloud_logger_name=None,
    enable_gcloud_logging=True,
    log_file_path="logs.txt",
    log_file_max_bytes=100 * 1024 * 1024,  # 100MB by default
    log_file_backup_count=5,  # 5 backup files by default
):
    """
    Set up logging configuration with both cloud and file handlers.
    This function ensures handlers are added only once.

    Args:
        logger_name: Name of the logger
        cloud_logger_name: Name for the cloud logging handler (used by Google Cloud Logging)
        enable_gcloud_logging: If True, attempts to set up Google Cloud Logging.
                               Set to False to avoid Google Cloud Logging initialization overhead.
        log_file_path: Path to the log file for RotatingFileHandler.
        log_file_max_bytes: Maximum size of the log file before rotation (in bytes).
        log_file_backup_count: Number of backup log files to keep.

    Returns:
        Configured logger instance
    """
    global _logging_configured
    if _logging_configured:
        # If already configured, just return the existing logger without re-adding handlers
        return logging.getLogger(logger_name)

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    # Conditionally initialize Google Cloud Logging client
    cloud_handler = None
    if enable_gcloud_logging and _GOOGLE_CLOUD_LOGGING_AVAILABLE:
        try:
            client = google.cloud.logging.Client()
            cloud_handler = CloudLoggingHandler(
                client, name=cloud_logger_name or logger_name
            )
            handlers.append(cloud_handler)
        except Exception as e:
            print(
                f"Notice: Could not initialize Google Cloud Logging. Functionality disabled: {e}"
            )
    elif enable_gcloud_logging and not _GOOGLE_CLOUD_LOGGING_AVAILABLE:
        print(
            "Warning: Google Cloud Logging requested but library is not available or failed to import."
        )

    rotation_handler = None
    if log_file_path is not None:
        try:
            rotation_handler = RotatingFileHandler(
                log_file_path,
                maxBytes=log_file_max_bytes,
                backupCount=log_file_backup_count,
            )
            handlers.append(rotation_handler)
        except Exception as e:
            print(
                f"Warning: Failed to initialize RotatingFileHandler: {e}. File logging is disabled."
            )
            rotation_handler = None  # Ensure it's None if creation failed

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,  # We re-enable force=True here because _logging_configured prevents redundant setups.
    )

    logging.info(f"LLL Logging initialized {handlers}")

    # Set the flag to True after successful configuration
    _logging_configured = True

    return logging.getLogger(logger_name)


def get_prefixed_logger(
    logger_name,
    prefix=None,
    cloud_logger_name=None,
    enable_gcloud_logging=False,
    log_file_path="logs.txt",
    log_file_max_bytes=100 * 1024 * 1024,
    log_file_backup_count=5,
):
    """
    Get a prefixed logger instance.
    The first call will set up the base logging configuration.

    Args:
        logger_name: Name of the logger
        prefix: The string to prefix messages with.
        cloud_logger_name: Name for the cloud logging handler (used by Google Cloud Logging)
        enable_gcloud_logging: If True, attempts to set up Google Cloud Logging.
                               Set to False to avoid Google Cloud Logging initialization overhead.
        log_file_path: Path to the log file for RotatingFileHandler.
        log_file_max_bytes: Maximum size of the log file before rotation.
        log_file_backup_count: Number of backup log files to keep.

    Returns:
        PrefixedLogger instance
    """
    setup_logging(
        logger_name,
        cloud_logger_name,
        enable_gcloud_logging=enable_gcloud_logging,
        log_file_path=log_file_path,
        log_file_max_bytes=log_file_max_bytes,
        log_file_backup_count=log_file_backup_count,
    )
    return PrefixedLogger(logger_name, prefix)

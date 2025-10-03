"""
Logging Middleware Configuration
"""

import os
import logging
import time
from flask import request, g
from google.cloud import logging as cloud_logging


def setup_logging(app):
    """
    Configure application logging
    """
    # Set log level from environment
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())

    # Configure root logger
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Suppress verbose logs from libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    # Request logging middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()

        # Log request details
        app.logger.info(
            f"Request: {request.method} {request.path} "
            f"- IP: {request.remote_addr} "
            f"- User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )

    @app.after_request
    def after_request(response):
        # Calculate request duration
        duration = round((time.time() - g.start_time) * 1000, 2)

        # Log response details
        app.logger.info(
            f"Response: {response.status_code} "
            f"- Duration: {duration}ms "
            f"- Size: {response.content_length or 0} bytes"
        )

        return response

    # Setup Cloud Logging for production
    if os.getenv("ENVIRONMENT") == "production":
        try:
            client = cloud_logging.Client()
            client.setup_logging()
            app.logger.info("Cloud Logging configured")
        except Exception as e:
            app.logger.warning(f"Failed to setup Cloud Logging: {e}")


class StructuredLogger:
    """
    Structured logger for consistent log formatting
    """

    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def log_event(self, level, event_type, message, **kwargs):
        """
        Log structured event with additional context
        """
        log_data = {
            "event_type": event_type,
            "message": message,
            "timestamp": time.time(),
            **kwargs,
        }

        self.logger.log(level, log_data)

    def log_api_call(self, method, endpoint, status_code, duration_ms, user_id=None):
        """
        Log API call with structured data
        """
        self.log_event(
            logging.INFO,
            "api_call",
            f"{method} {endpoint}",
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
        )

    def log_business_event(self, event_type, entity_id, action, user_id=None, **kwargs):
        """
        Log business events (order created, delivery completed, etc.)
        """
        self.log_event(
            logging.INFO,
            "business_event",
            f"{event_type}: {action}",
            entity_id=entity_id,
            user_id=user_id,
            **kwargs,
        )

    def log_error(self, error, context=None):
        """
        Log error with context
        """
        self.log_event(
            logging.ERROR,
            "error",
            str(error),
            error_type=type(error).__name__,
            context=context,
        )

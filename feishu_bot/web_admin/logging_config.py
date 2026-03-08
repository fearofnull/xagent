"""
Logging Configuration Module

This module provides comprehensive logging configuration for the web admin interface.
Configures log format, levels, handlers, and request/error logging.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from flask import Flask, request, g
from functools import wraps


def configure_logging(
    app: Flask,
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    enable_file_logging: bool = True
) -> None:
    """Configure comprehensive logging for the web admin interface
    
    Args:
        app: Flask application instance
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: logs/)
        enable_file_logging: Whether to enable file logging
    """
    # Create log directory if needed
    if enable_file_logging:
        if log_dir is None or log_dir == '':
            log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Define log format
    log_format = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file_logging:
        # General application log (rotating)
        app_log_file = os.path.join(log_dir, "web_admin.log")
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        app_handler.setLevel(logging.INFO)
        app_handler.setFormatter(log_format)
        root_logger.addHandler(app_handler)
        
        # Error log (rotating)
        error_log_file = os.path.join(log_dir, "web_admin_error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(log_format)
        root_logger.addHandler(error_handler)
        
        # Access log (rotating) - for API requests
        access_log_file = os.path.join(log_dir, "web_admin_access.log")
        access_handler = logging.handlers.RotatingFileHandler(
            access_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        access_handler.setFormatter(log_format)
        
        # Create access logger
        access_logger = logging.getLogger('web_admin.access')
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False  # Don't propagate to root logger
        
        # Authentication log (rotating) - for auth attempts
        auth_log_file = os.path.join(log_dir, "web_admin_auth.log")
        auth_handler = logging.handlers.RotatingFileHandler(
            auth_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        auth_handler.setLevel(logging.INFO)
        auth_handler.setFormatter(log_format)
        
        # Create auth logger
        auth_logger = logging.getLogger('web_admin.auth')
        auth_logger.addHandler(auth_handler)
        auth_logger.setLevel(logging.INFO)
        auth_logger.propagate = False  # Don't propagate to root logger
    
    # Configure Flask app logger
    app.logger.setLevel(getattr(logging, log_level.upper()))
    
    # Register request logging middleware
    register_request_logging(app)
    
    logging.info(f"Logging configured: level={log_level}, file_logging={enable_file_logging}")


def register_request_logging(app: Flask) -> None:
    """Register middleware to log all API requests and responses
    
    Args:
        app: Flask application instance
    """
    access_logger = logging.getLogger('web_admin.access')
    
    @app.before_request
    def log_request_start():
        """Log the start of each request"""
        g.request_start_time = datetime.now()
        
        # Log request details
        access_logger.info(
            f"Request started: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )
        
        # Log request body for POST/PUT (excluding sensitive data)
        if request.method in ['POST', 'PUT'] and request.is_json:
            data = request.get_json()
            # Mask password field
            if isinstance(data, dict) and 'password' in data:
                data = {**data, 'password': '***'}
            access_logger.debug(f"Request body: {data}")
    
    @app.after_request
    def log_request_end(response):
        """Log the end of each request with response status"""
        if hasattr(g, 'request_start_time'):
            duration = (datetime.now() - g.request_start_time).total_seconds()
            
            access_logger.info(
                f"Request completed: {request.method} {request.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )
        
        return response
    
    @app.errorhandler(Exception)
    def log_unhandled_exception(error):
        """Log unhandled exceptions"""
        access_logger.error(
            f"Unhandled exception in {request.method} {request.path}: {error}",
            exc_info=True
        )
        # Re-raise to let Flask handle it
        raise


def log_authentication_attempt(
    success: bool,
    username: str = "admin",
    ip_address: Optional[str] = None,
    reason: Optional[str] = None
) -> None:
    """Log authentication attempts
    
    Args:
        success: Whether authentication was successful
        username: Username attempting to authenticate
        ip_address: IP address of the client
        reason: Reason for failure (if applicable)
    """
    auth_logger = logging.getLogger('web_admin.auth')
    
    if success:
        auth_logger.info(
            f"Authentication successful: user={username} ip={ip_address}"
        )
    else:
        auth_logger.warning(
            f"Authentication failed: user={username} ip={ip_address} reason={reason}"
        )


def log_api_error(
    endpoint: str,
    error: Exception,
    status_code: int,
    user: Optional[str] = None
) -> None:
    """Log API errors with context
    
    Args:
        endpoint: API endpoint where error occurred
        error: Exception that was raised
        status_code: HTTP status code returned
        user: User who made the request (if authenticated)
    """
    logger = logging.getLogger('web_admin.api')
    
    logger.error(
        f"API error in {endpoint}: {type(error).__name__}: {error} "
        f"(status={status_code}, user={user})",
        exc_info=True
    )


def log_config_change(
    session_id: str,
    action: str,
    user: str,
    changes: Optional[dict] = None
) -> None:
    """Log configuration changes for audit trail
    
    Args:
        session_id: Session ID being modified
        action: Action performed (create, update, delete)
        user: User who made the change
        changes: Dictionary of changed fields (optional)
    """
    logger = logging.getLogger('web_admin.config')
    
    if changes:
        logger.info(
            f"Config {action}: session={session_id} user={user} changes={changes}"
        )
    else:
        logger.info(
            f"Config {action}: session={session_id} user={user}"
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

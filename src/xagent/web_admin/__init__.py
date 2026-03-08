"""
Web Admin Interface for Feishu Bot Configuration Management

This module provides a web-based interface for managing bot configurations,
including viewing, editing, and resetting session configurations.
"""

from .server import WebAdminServer
from .auth import AuthManager
from .utils import (
    WebAdminError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    InternalError,
    handle_errors,
    format_error_response,
    format_success_response,
    get_status_code_for_error
)

__version__ = "1.0.0"

__all__ = [
    'WebAdminServer',
    'AuthManager',
    'WebAdminError',
    'ValidationError',
    'AuthenticationError',
    'NotFoundError',
    'InternalError',
    'handle_errors',
    'format_error_response',
    'format_success_response',
    'get_status_code_for_error'
]

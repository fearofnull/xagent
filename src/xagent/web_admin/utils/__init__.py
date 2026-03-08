"""Web Admin Utils Module

This module contains utility functions and classes for the web admin interface.
"""

from .json_utils import dump, load, dumps, loads
from .cache import SimpleCache, cached
from .errors import (
    WebAdminError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
    InternalError,
    handle_errors,
    get_status_code_for_error,
    format_error_response,
    format_success_response
)

__all__ = [
    'dump',
    'load',
    'dumps',
    'loads',
    'SimpleCache',
    'cached',
    'WebAdminError',
    'ValidationError',
    'AuthenticationError',
    'NotFoundError',
    'InternalError',
    'handle_errors',
    'get_status_code_for_error',
    'format_error_response',
    'format_success_response'
]
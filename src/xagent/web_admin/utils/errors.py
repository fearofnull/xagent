"""
Error Handling Module

This module provides unified error handling for the web admin interface.
Defines error response formats, custom exceptions, and error handling decorators.
"""

import logging
from functools import wraps
from typing import Dict, Any, Optional, Tuple
from flask import jsonify

logger = logging.getLogger(__name__)


# ==================== Custom Exception Classes ====================

class WebAdminError(Exception):
    """Base exception for web admin errors"""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        field: Optional[str] = None
    ):
        """Initialize web admin error
        
        Args:
            message: User-friendly error message
            code: Error code for programmatic handling
            status_code: HTTP status code
            field: Field name if error is related to a specific field
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.field = field


class ValidationError(WebAdminError):
    """Validation error (400 Bad Request)"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            field=field
        )


class AuthenticationError(WebAdminError):
    """Authentication error (401 Unauthorized)"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401
        )


class NotFoundError(WebAdminError):
    """Resource not found error (404 Not Found)"""
    
    def __init__(self, message: str, resource_type: str = "Resource"):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404
        )
        self.resource_type = resource_type


class InternalError(WebAdminError):
    """Internal server error (500 Internal Server Error)"""
    
    def __init__(self, message: str = "An internal error occurred"):
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            status_code=500
        )


# ==================== Error Response Formatting ====================

def format_error_response(
    error: Exception,
    status_code: int = 500,
    code: str = "INTERNAL_ERROR",
    field: Optional[str] = None
) -> Tuple[Dict[str, Any], int]:
    """Format error as JSON response
    
    Args:
        error: Exception object
        status_code: HTTP status code
        code: Error code
        field: Field name if applicable
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    error_response = {
        'success': False,
        'data': None,
        'error': {
            'code': code,
            'message': str(error)
        }
    }
    
    if field:
        error_response['error']['field'] = field
    
    return error_response, status_code


def format_success_response(
    data: Any = None,
    message: str = "Operation successful"
) -> Dict[str, Any]:
    """Format success response
    
    Args:
        data: Response data
        message: Success message
    
    Returns:
        Response dictionary
    """
    return {
        'success': True,
        'data': data,
        'message': message
    }


# ==================== Error Handling Decorator ====================

def handle_errors(f):
    """Decorator to handle errors in API endpoints
    
    Catches exceptions and returns properly formatted error responses.
    Logs errors for debugging and monitoring.
    
    Usage:
        @app.route('/api/endpoint')
        @handle_errors
        def my_endpoint():
            # Your code here
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except WebAdminError as e:
            # Custom web admin errors - already have proper formatting
            logger.warning(f"Web admin error in {f.__name__}: {e.message}")
            
            error_response = {
                'success': False,
                'data': None,
                'error': {
                    'code': e.code,
                    'message': e.message
                }
            }
            
            if e.field:
                error_response['error']['field'] = e.field
            
            return jsonify(error_response), e.status_code
        
        except ValueError as e:
            # Value errors - typically validation issues
            logger.warning(f"Validation error in {f.__name__}: {e}")
            
            error_response = {
                'success': False,
                'data': None,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e)
                }
            }
            
            return jsonify(error_response), 400
        
        except KeyError as e:
            # Missing required fields
            logger.warning(f"Missing field in {f.__name__}: {e}")
            
            error_response = {
                'success': False,
                'data': None,
                'error': {
                    'code': 'MISSING_FIELD',
                    'message': f'Missing required field: {str(e)}'
                }
            }
            
            return jsonify(error_response), 400
        
        except Exception as e:
            # Unexpected errors - log with full traceback
            logger.error(f"Unexpected error in {f.__name__}: {e}", exc_info=True)
            
            error_response = {
                'success': False,
                'data': None,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An internal error occurred'
                }
            }
            
            return jsonify(error_response), 500
    
    return decorated_function


# ==================== HTTP Status Code Mapping ====================

# Standard HTTP status codes used in the API
HTTP_STATUS_CODES = {
    # Success codes
    'OK': 200,
    'CREATED': 201,
    'NO_CONTENT': 204,
    
    # Client error codes
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'CONFLICT': 409,
    'UNPROCESSABLE_ENTITY': 422,
    
    # Server error codes
    'INTERNAL_SERVER_ERROR': 500,
    'SERVICE_UNAVAILABLE': 503
}


# Error code to HTTP status code mapping
ERROR_CODE_TO_STATUS = {
    # Authentication errors
    'AUTHENTICATION_ERROR': HTTP_STATUS_CODES['UNAUTHORIZED'],
    'INVALID_CREDENTIALS': HTTP_STATUS_CODES['UNAUTHORIZED'],
    'INVALID_TOKEN': HTTP_STATUS_CODES['UNAUTHORIZED'],
    'TOKEN_EXPIRED': HTTP_STATUS_CODES['UNAUTHORIZED'],
    
    # Validation errors
    'VALIDATION_ERROR': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_FIELD': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_PASSWORD': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_FILE': HTTP_STATUS_CODES['BAD_REQUEST'],
    'EMPTY_FILENAME': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_PROVIDER': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_CLI_PROVIDER': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_LAYER': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_JSON': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_ENCODING': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_FORMAT': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_CONFIGS': HTTP_STATUS_CODES['BAD_REQUEST'],
    'INVALID_CONFIGS_FORMAT': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_REQUIRED_FIELDS': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_CONFIG_FIELDS': HTTP_STATUS_CODES['BAD_REQUEST'],
    'MISSING_METADATA_FIELDS': HTTP_STATUS_CODES['BAD_REQUEST'],
    
    # Not found errors
    'NOT_FOUND': HTTP_STATUS_CODES['NOT_FOUND'],
    'CONFIG_NOT_FOUND': HTTP_STATUS_CODES['NOT_FOUND'],
    
    # Internal errors
    'INTERNAL_ERROR': HTTP_STATUS_CODES['INTERNAL_SERVER_ERROR'],
    'FILE_ERROR': HTTP_STATUS_CODES['INTERNAL_SERVER_ERROR'],
    'DATABASE_ERROR': HTTP_STATUS_CODES['INTERNAL_SERVER_ERROR']
}


def get_status_code_for_error(error_code: str) -> int:
    """Get HTTP status code for error code
    
    Args:
        error_code: Error code string
    
    Returns:
        HTTP status code (defaults to 500 if not found)
    """
    return ERROR_CODE_TO_STATUS.get(error_code, HTTP_STATUS_CODES['INTERNAL_SERVER_ERROR'])

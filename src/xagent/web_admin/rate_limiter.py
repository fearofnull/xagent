"""
Rate Limiter Module

This module implements rate limiting for API endpoints to prevent abuse.
Uses Flask-Limiter with in-memory storage for rate limit tracking.
"""

import logging
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)


def get_rate_limit_key():
    """Get the key for rate limiting
    
    Uses IP address for unauthenticated requests.
    For authenticated requests, could be extended to use user ID from token.
    
    Returns:
        str: The rate limit key (IP address)
    """
    return get_remote_address()


def create_limiter(app: Flask) -> Limiter:
    """Create and configure rate limiter
    
    Args:
        app: Flask application instance
    
    Returns:
        Limiter: Configured rate limiter instance
    """
    # Create limiter with in-memory storage
    limiter = Limiter(
        app=app,
        key_func=get_rate_limit_key,
        default_limits=["200 per day", "50 per hour"],  # Default limits for all routes
        storage_uri="memory://",  # In-memory storage (simple, no external dependencies)
        strategy="fixed-window",  # Fixed window strategy
        headers_enabled=True,  # Include rate limit headers in responses
    )
    
    logger.info("Rate limiter initialized with in-memory storage")
    return limiter


def configure_rate_limits(limiter: Limiter):
    """Configure specific rate limits for different endpoint categories
    
    This function defines rate limit decorators that can be applied to routes.
    
    Args:
        limiter: Limiter instance
    
    Returns:
        dict: Dictionary of rate limit decorators for different endpoint types
    """
    # Login endpoint: Strict rate limit to prevent brute force attacks
    # 5 attempts per minute per IP
    login_limit = limiter.limit(
        "5 per minute",
        error_message="Too many login attempts. Please try again later."
    )
    
    # API endpoints: Moderate rate limit for general API usage
    # 60 requests per minute per IP
    api_limit = limiter.limit(
        "60 per minute",
        error_message="API rate limit exceeded. Please slow down your requests."
    )
    
    # Export/Import endpoints: Lower rate limit for resource-intensive operations
    # 10 requests per minute per IP
    export_import_limit = limiter.limit(
        "10 per minute",
        error_message="Export/import rate limit exceeded. Please wait before trying again."
    )
    
    logger.info("Rate limit configurations created")
    
    return {
        'login': login_limit,
        'api': api_limit,
        'export_import': export_import_limit
    }


def handle_rate_limit_exceeded(e):
    """Custom error handler for rate limit exceeded
    
    Args:
        e: RateLimitExceeded exception
    
    Returns:
        tuple: JSON response and status code
    """
    logger.warning(f"Rate limit exceeded for {request.remote_addr} on {request.path}")
    
    return {
        'success': False,
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': str(e.description)
        }
    }, 429

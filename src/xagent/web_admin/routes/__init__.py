"""API Routes Module

This module contains all the API routes for the web admin interface.
"""

from .api_routes import register_api_routes
from .provider_api_routes import register_provider_api_routes

__all__ = [
    'register_api_routes',
    'register_provider_api_routes'
]
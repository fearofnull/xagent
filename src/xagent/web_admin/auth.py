"""
Authentication Module

This module handles authentication and authorization for the web admin interface.
Uses JWT tokens for stateless authentication.
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify
from .logging_config import log_authentication_attempt
from .utils import WebAdminError, AuthenticationError

logger = logging.getLogger(__name__)


class AuthManager:
    """Authentication Manager
    
    Manages password verification and JWT token generation/validation.
    """
    
    def __init__(self, secret_key: str, admin_password: str):
        """Initialize Authentication Manager
        
        Args:
            secret_key: Secret key for JWT token signing
            admin_password: Admin password for login
        """
        self.secret_key = secret_key
        self.admin_password = admin_password
        self.token_expiry_hours = 2  # Token valid for 2 hours
        
        logger.info("AuthManager initialized")
    
    def verify_password(self, password: str, ip_address: Optional[str] = None) -> bool:
        """Verify admin password
        
        Args:
            password: Password to verify
            ip_address: IP address of the client (for logging)
            
        Returns:
            True if password is correct, False otherwise
        """
        is_valid = password == self.admin_password
        
        # Log authentication attempt
        log_authentication_attempt(
            success=is_valid,
            username="admin",
            ip_address=ip_address,
            reason="Invalid password" if not is_valid else None
        )
        
        return is_valid
    
    def generate_token(self) -> Dict[str, Any]:
        """Generate JWT access token
        
        Returns:
            Dictionary containing token and expiry information
        """
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.token_expiry_hours)
        
        payload = {
            'iat': now,  # Issued at
            'exp': expiry,  # Expiration time
            'sub': 'admin'  # Subject (user identifier)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        return {
            'token': token,
            'expires_in': self.token_expiry_hours * 3600,  # In seconds
            'expires_at': expiry.isoformat()
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT access token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def require_auth(self, f):
        """Decorator to require authentication for API endpoints
        
        Args:
            f: Function to decorate
            
        Returns:
            Decorated function that checks authentication
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'UNAUTHORIZED',
                        'message': 'Authorization header missing'
                    }
                }), 401
            
            # Extract token from "Bearer <token>" format
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_AUTH_HEADER',
                        'message': 'Invalid authorization header format'
                    }
                }), 401
            
            token = parts[1]
            
            # Verify token
            payload = self.verify_token(token)
            if not payload:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TOKEN',
                        'message': 'Invalid or expired token'
                    }
                }), 401
            
            # Token is valid, proceed with request
            return f(*args, **kwargs)
        
        return decorated_function

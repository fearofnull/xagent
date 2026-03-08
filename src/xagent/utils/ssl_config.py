"""
SSL Certificate Configuration Module

This module provides SSL certificate configuration for secure HTTPS connections
to the Feishu API. It uses the certifi library to provide trusted CA certificates.

Requirements:
- Requirement 8.1: Set SSL_CERT_FILE environment variable to certifi certificate bundle path
- Requirement 8.2: Clear SSL_CERT_DIR environment variable
- Requirement 8.3: Use configured SSL certificates for all HTTPS requests
"""

import os
import logging
import certifi

logger = logging.getLogger(__name__)


def configure_ssl() -> None:
    """
    Configure SSL certificates for HTTPS connections.
    
    This function should be called during application startup to ensure
    all HTTPS requests use the correct SSL certificates.
    
    Actions:
    1. Sets SSL_CERT_FILE environment variable to the certifi certificate bundle path
    2. Clears SSL_CERT_DIR environment variable to avoid conflicts
    
    Requirements:
    - Requirement 8.1: Set SSL_CERT_FILE to certifi certificate path
    - Requirement 8.2: Clear SSL_CERT_DIR environment variable
    
    Example:
        >>> from xagent.utils.ssl_config import configure_ssl
        >>> configure_ssl()
        >>> # Now all HTTPS requests will use the configured certificates
    """
    try:
        # Get the path to certifi's certificate bundle
        cert_path = certifi.where()
        
        # Set SSL_CERT_FILE environment variable
        os.environ['SSL_CERT_FILE'] = cert_path
        logger.info(f"SSL_CERT_FILE set to: {cert_path}")
        
        # Clear SSL_CERT_DIR to avoid conflicts
        if 'SSL_CERT_DIR' in os.environ:
            del os.environ['SSL_CERT_DIR']
            logger.info("SSL_CERT_DIR cleared")
        
        logger.info("SSL certificate configuration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to configure SSL certificates: {e}")
        raise


def get_ssl_cert_path() -> str:
    """
    Get the current SSL certificate file path.
    
    Returns:
        str: Path to the SSL certificate file, or empty string if not configured
    
    Example:
        >>> from xagent.utils.ssl_config import get_ssl_cert_path
        >>> cert_path = get_ssl_cert_path()
        >>> print(cert_path)
        /path/to/certifi/cacert.pem
    """
    return os.environ.get('SSL_CERT_FILE', '')


def is_ssl_configured() -> bool:
    """
    Check if SSL certificates are properly configured.
    
    Returns:
        bool: True if SSL_CERT_FILE is set and SSL_CERT_DIR is not set
    
    Example:
        >>> from xagent.utils.ssl_config import is_ssl_configured
        >>> if not is_ssl_configured():
        ...     configure_ssl()
    """
    return (
        'SSL_CERT_FILE' in os.environ and
        os.environ['SSL_CERT_FILE'] != '' and
        'SSL_CERT_DIR' not in os.environ
    )

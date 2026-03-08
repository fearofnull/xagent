"""
WSGI Entry Point for Feishu Bot Web Admin Interface

This module provides a WSGI-compatible application instance for
production deployment with Gunicorn or other WSGI servers.

Usage with Gunicorn:
    gunicorn -c gunicorn.conf.py wsgi:app

Environment Variables:
    WEB_ADMIN_PASSWORD: Admin password for authentication (required)
    JWT_SECRET_KEY: Secret key for JWT token signing (required)
    WEB_ADMIN_STATIC_FOLDER: Path to frontend static files (optional)
    WEB_ADMIN_LOG_LEVEL: Logging level (default: INFO)
    WEB_ADMIN_LOG_DIR: Directory for log files (default: logs/)
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.xagent.core.config_manager import ConfigManager
from src.xagent.web_admin.server import WebAdminServer

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
required_vars = ['WEB_ADMIN_PASSWORD', 'JWT_SECRET_KEY']
missing_vars = [var for var in required_vars if not os.environ.get(var)]

if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these variables in your .env file or environment.")
    sys.exit(1)

# Get configuration from environment
admin_password = os.environ.get('WEB_ADMIN_PASSWORD')
jwt_secret_key = os.environ.get('JWT_SECRET_KEY')
static_folder = os.environ.get('WEB_ADMIN_STATIC_FOLDER')
log_level = os.environ.get('WEB_ADMIN_LOG_LEVEL', 'INFO')
log_dir = os.environ.get('WEB_ADMIN_LOG_DIR', 'logs')

# Initialize ConfigManager
config_manager = ConfigManager()

# Create WebAdminServer instance
# Note: host and port are configured in gunicorn.conf.py
server = WebAdminServer(
    config_manager=config_manager,
    host='0.0.0.0',  # Will be overridden by Gunicorn
    port=5000,       # Will be overridden by Gunicorn
    admin_password=admin_password,
    jwt_secret_key=jwt_secret_key,
    static_folder=static_folder,
    log_level=log_level,
    log_dir=log_dir
)

# Export Flask app for WSGI server
app = server.app

# Log startup information
if __name__ != "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.info("WSGI application initialized")
    logger.info(f"Static folder: {static_folder or 'Not configured'}")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log directory: {log_dir}")

"""
Web Admin Server Module

This module implements the Flask web server for the admin interface.
It provides HTTP API endpoints and static file serving for the frontend.
"""

import os
import logging
from typing import Optional
from flask import Flask, send_from_directory
from flask_cors import CORS

from ..core.config_manager import ConfigManager
from .auth import AuthManager
from .routes import register_api_routes, register_provider_api_routes
from .routes.cron_api_routes import register_cron_api_routes
from .logging_config import configure_logging
from .rate_limiter import create_limiter, configure_rate_limits, handle_rate_limit_exceeded
from .response_compression import configure_compression
from .utils import dump, load

logger = logging.getLogger(__name__)

class WebAdminServer:
    """Web Admin Interface Server
    
    Provides a web-based interface for managing bot configurations.
    Supports RESTful API endpoints and static file serving.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        cron_manager = None,
        host: str = "0.0.0.0",
        port: int = 5000,
        admin_password: Optional[str] = None,
        jwt_secret_key: Optional[str] = None,
        static_folder: Optional[str] = None,
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        enable_rate_limiting: bool = True
    ):
        """Initialize Web Admin Server
        
        Args:
            config_manager: Configuration manager instance
            cron_manager: CronManager instance (optional)
            host: Server host address (default: 0.0.0.0)
            port: Server port (default: 5000)
            admin_password: Admin password for authentication
            jwt_secret_key: Secret key for JWT token signing
            static_folder: Path to frontend static files (optional)
            log_level: Logging level (default: INFO)
            log_dir: Directory for log files (default: logs/)
            enable_rate_limiting: Enable rate limiting (default: True)
        """
        self.config_manager = config_manager
        self.cron_manager = cron_manager
        self.host = host
        self.port = port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # Configure logging first
        configure_logging(
            self.app,
            log_level=log_level,
            log_dir=log_dir,
            enable_file_logging=True
        )
        
        # Configure CORS based on environment
        self._configure_cors()
        
        # Configure response compression
        configure_compression(self.app, min_size=500, compression_level=6)
        
        # Initialize rate limiter if enabled
        self.rate_limiter = None
        self.rate_limits = None
        if enable_rate_limiting:
            self.rate_limiter = create_limiter(self.app)
            self.rate_limits = configure_rate_limits(self.rate_limiter)
            
            # Register custom error handler for rate limit exceeded
            from flask_limiter.errors import RateLimitExceeded
            self.app.errorhandler(RateLimitExceeded)(handle_rate_limit_exceeded)
            
            logger.info("Rate limiting enabled")
        else:
            logger.info("Rate limiting disabled")
        
        # Initialize authentication manager
        self.auth_manager = AuthManager(
            secret_key=jwt_secret_key or os.environ.get("JWT_SECRET_KEY", "dev-secret-key"),
            admin_password=admin_password or os.environ.get("WEB_ADMIN_PASSWORD", "admin123")
        )
        
        # Initialize provider config manager
        from ..core.provider_config_manager import ProviderConfigManager
        self.provider_config_manager = ProviderConfigManager(
            storage_path="./data/provider_configs.json"
        )
        
        # Register API routes (pass rate_limits if available)
        register_api_routes(
            self.app, 
            self.config_manager, 
            self.auth_manager,
            rate_limits=self.rate_limits
        )
        
        # Register provider API routes
        register_provider_api_routes(
            self.app,
            self.provider_config_manager,
            self.auth_manager,
            rate_limits=self.rate_limits
        )
        
        # Register cron API routes if cron_manager is provided
        if self.cron_manager:
            register_cron_api_routes(
                self.app,
                self.cron_manager,
                self.auth_manager,
                rate_limits=self.rate_limits
            )
        
        # Determine static folder path
        if static_folder is None or static_folder == '':
            # Default to static folder in the same directory as this module
            module_dir = os.path.dirname(os.path.abspath(__file__))
            static_folder = os.path.join(module_dir, 'static')
        else:
            # Convert relative path to absolute path
            static_folder = os.path.abspath(static_folder)
        
        # Configure static file serving if folder exists
        if os.path.exists(static_folder):
            self._configure_static_files(static_folder)
            logger.info(f"Serving static files from: {static_folder}")
        else:
            logger.warning(f"Static folder not found: {static_folder}")
            
            # Add a default route to handle all requests when static folder doesn't exist
            @self.app.route('/', defaults={'path': ''})
            @self.app.route('/<path:path>')
            def default_route(path):
                return "<h1>Web Admin Interface</h1><p>Static files not found. Please build the frontend first.</p>", 200
        
        logger.info(f"Web Admin Server initialized on {host}:{port}")
    
    def _configure_cors(self):
        """Configure CORS based on environment
        
        In development: Allow all origins for easier testing
        In production: Restrict to specific allowed origins from environment variable
        """
        # Get environment (default to production for safety)
        env = os.environ.get("FLASK_ENV", "production").lower()
        
        if env == "development":
            # Development: Allow all origins
            CORS(self.app, resources={
                r"/api/*": {
                    "origins": "*",
                    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Authorization"],
                    "expose_headers": ["Content-Type", "Authorization"],
                    "supports_credentials": False
                }
            })
            logger.info("CORS configured for development: allowing all origins")
        else:
            # Production: Restrict to specific origins
            allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
            
            if allowed_origins:
                # Parse comma-separated origins
                origins_list = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]
                
                CORS(self.app, resources={
                    r"/api/*": {
                        "origins": origins_list,
                        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                        "allow_headers": ["Content-Type", "Authorization"],
                        "expose_headers": ["Content-Type", "Authorization"],
                        "supports_credentials": True
                    }
                })
                logger.info(f"CORS configured for production: allowing origins {origins_list}")
            else:
                # No origins specified, use restrictive default (localhost only)
                default_origins = ["http://localhost:5000", "http://127.0.0.1:5000"]
                
                CORS(self.app, resources={
                    r"/api/*": {
                        "origins": default_origins,
                        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                        "allow_headers": ["Content-Type", "Authorization"],
                        "expose_headers": ["Content-Type", "Authorization"],
                        "supports_credentials": True
                    }
                })
                logger.warning(
                    f"CORS_ALLOWED_ORIGINS not set in production, using default: {default_origins}. "
                    "Set CORS_ALLOWED_ORIGINS environment variable to specify allowed origins."
                )
    
    def _configure_static_files(self, static_folder: str):
        """Configure static file serving for frontend
        
        Args:
            static_folder: Path to frontend build output
        """
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def serve_static(path):
            """Serve static files and handle SPA routing
            
            This function serves static files from the build output directory.
            For any route that doesn't match a static file, it returns index.html
            to support client-side routing in the Vue.js SPA.
            
            API routes are handled separately and won't reach this function.
            """
            # If path is empty, serve index.html
            if not path:
                return send_from_directory(static_folder, 'index.html')
            
            # Check if the requested file exists
            file_path = os.path.join(static_folder, path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Serve the static file
                return send_from_directory(static_folder, path)
            
            # For all other routes (SPA routes), serve index.html
            # This allows Vue Router to handle the routing on the client side
            return send_from_directory(static_folder, 'index.html')
    
    def start(self, debug: bool = False):
        """Start the web server
        
        Args:
            debug: Enable debug mode (default: False)
        """
        logger.info(f"Starting Web Admin Server at http://{self.host}:{self.port}")
        print(f"\n{'='*60}")
        print(f"Web Admin Interface is running!")
        print(f"Access URL: http://{self.host}:{self.port}")
        print(f"{'='*60}\n")
        
        try:
            # 尝试使用 waitress (生产级 WSGI 服务器)
            try:
                from waitress import serve
                logger.info("Using Waitress WSGI server (production-ready)")
                serve(
                    self.app,
                    host=self.host,
                    port=self.port,
                    threads=4,  # 线程数
                    channel_timeout=60,
                    cleanup_interval=30,
                    _quiet=False
                )
            except ImportError:
                # 如果 waitress 未安装,回退到 Flask 内置服务器
                logger.warning("Waitress not installed, using Flask development server")
                logger.warning("For production, install waitress: pip install waitress")
                
                # 禁用 Werkzeug 的开发服务器警告
                os.environ['WERKZEUG_RUN_MAIN'] = 'true'
                
                self.app.run(
                    host=self.host, 
                    port=self.port, 
                    debug=debug,
                    use_reloader=False,
                    threaded=True
                )
        except KeyboardInterrupt:
            logger.info("Web Admin Server stopped by user")
            self.stop()
    
    def stop(self):
        """Stop the web server gracefully
        
        Ensures all pending configuration changes are saved.
        """
        logger.info("Stopping Web Admin Server...")
        # ConfigManager handles auto-save, no additional action needed
        logger.info("Web Admin Server stopped")

def main():
    """Command-line entry point for Web Admin Server"""
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Feishu Bot Web Admin Interface")
    parser.add_argument("--host", default="0.0.0.0", help="Server host address")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--static-folder", help="Path to frontend static files")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Logging level")
    parser.add_argument("--log-dir", help="Directory for log files")
    parser.add_argument("--disable-rate-limiting", action="store_true",
                       help="Disable rate limiting (not recommended for production)")
    
    args = parser.parse_args()
    
    # Check required environment variables
    admin_password = os.environ.get("WEB_ADMIN_PASSWORD")
    if not admin_password:
        print("WARNING: WEB_ADMIN_PASSWORD not set, using default password 'admin123'")
    
    jwt_secret = os.environ.get("JWT_SECRET_KEY")
    if not jwt_secret:
        print("WARNING: JWT_SECRET_KEY not set, using development key")
    
    # Load global configuration from environment
    from ..config import BotConfig
    try:
        global_config = BotConfig.from_env()
        print(f"✅ Global configuration loaded")
        print(f"   - TARGET_PROJECT_DIR: {global_config.target_directory or '(not set)'}")
        print(f"   - RESPONSE_LANGUAGE: {global_config.response_language or '(not set)'}")
        print(f"   - DEFAULT_CLI_PROVIDER: {global_config.default_cli_provider or '(not set)'}")
    except Exception as e:
        print(f"WARNING: Failed to load global configuration: {e}")
        global_config = None
    
    # Initialize ConfigManager with global config
    config_manager = ConfigManager(global_config=global_config)
    
    # Create and start server
    server = WebAdminServer(
        config_manager=config_manager,
        host=args.host,
        port=args.port,
        admin_password=admin_password,
        jwt_secret_key=jwt_secret,
        static_folder=args.static_folder,
        log_level=args.log_level,
        log_dir=args.log_dir,
        enable_rate_limiting=not args.disable_rate_limiting
    )
    
    server.start(debug=args.debug)

if __name__ == "__main__":
    main()

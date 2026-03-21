"""
API Routes Module

This module defines all RESTful API endpoints for the web admin interface.
Provides endpoints for authentication, configuration management, and data export/import.
"""

import logging
from flask import Flask, request, jsonify, send_file
from typing import Dict, Any

from ...core.config_manager import ConfigManager
from ..auth import AuthManager
from ..logging_config import log_api_error, log_config_change

logger = logging.getLogger(__name__)

def register_api_routes(
    app: Flask, 
    config_manager: ConfigManager, 
    auth_manager: AuthManager,
    rate_limits: dict = None,
    tool_state_manager = None
):
    """Register all API routes with the Flask app
    
    Args:
        app: Flask application instance
        config_manager: Configuration manager instance
        auth_manager: Authentication manager instance
        rate_limits: Dictionary of rate limit decorators (optional)
    """
    
    # Helper function to apply rate limit if available
    def apply_rate_limit(route_func, limit_type):
        """Apply rate limit decorator if available"""
        if rate_limits and limit_type in rate_limits:
            return rate_limits[limit_type](route_func)
        return route_func
    
    # ==================== Health Check Route ====================
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for Docker and monitoring
        
        Response:
            {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        """
        from datetime import datetime
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    
    # ==================== Authentication Routes ====================
    
    def _login():
        """Login endpoint
        
        Request body:
            {
                "password": "admin_password"
            }
        
        Response:
            {
                "success": true,
                "data": {
                    "token": "jwt_token",
                    "expires_in": 7200,
                    "expires_at": "2024-01-01T12:00:00"
                },
                "message": "Login successful"
            }
        """
        try:
            data = request.get_json()
            password = data.get('password')
            
            if not password:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_PASSWORD',
                        'message': 'Password is required'
                    }
                }), 400
            
            # Verify password
            if not auth_manager.verify_password(password, request.remote_addr):
                logger.warning(f"Failed login attempt from {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': 'Invalid password'
                    }
                }), 401
            
            # Generate token
            token_data = auth_manager.generate_token()
            
            logger.info("User logged in successfully")
            return jsonify({
                'success': True,
                'data': token_data,
                'message': 'Login successful'
            }), 200
            
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            log_api_error(
                endpoint='/api/auth/login',
                error=e,
                status_code=500,
                user=None
            )
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'An error occurred during login'
                }
            }), 500
    
    # Apply rate limit and register route
    login = apply_rate_limit(_login, 'login')
    app.route('/api/auth/login', methods=['POST'])(login)
    
    @app.route('/api/auth/logout', methods=['POST'])
    @auth_manager.require_auth
    def logout():
        """Logout endpoint
        
        Response:
            {
                "success": true,
                "message": "Logout successful"
            }
        """
        # Token-based auth is stateless, client will discard token
        logger.info("User logged out")
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
    
    # ==================== Configuration Routes ====================
    
    @app.route('/api/configs/options', methods=['GET'])
    @auth_manager.require_auth
    def get_config_options():
        """Get available configuration options
        
        Response:
            {
                "success": true,
                "data": {
                    "layers": ["api", "cli"],
                    "cli_providers": ["claude", "gemini", "qwen"]
                }
            }
        """
        try:
            return jsonify({
                'success': True,
                'data': {
                    'layers': config_manager.VALID_LAYERS,
                    'cli_providers': config_manager.VALID_CLI_PROVIDERS
                }
            }), 200
        except Exception as e:
            logger.error(f"Error getting config options: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve configuration options'
                }
            }), 500
    
    def _get_configs():
        """Get all session configurations
        
        Query parameters:
            - session_type: Filter by session type (user/group)
            - search: Search by session_id
            - sort: Sort by field (default: updated_at)
            - order: Sort order (asc/desc, default: desc)
        
        Response:
            {
                "success": true,
                "data": [
                    {
                        "session_id": "ou_xxx",
                        "session_type": "user",
                        "config": {...},
                        "metadata": {...}
                    }
                ]
            }
        """
        try:
            # Get all configurations from ConfigManager
            all_configs = []
            for session_id, config in config_manager.configs.items():
                config_dict = {
                    'session_id': config.session_id,
                    'session_type': config.session_type,
                    'config': {
                        'target_project_dir': config.target_project_dir,
                        'response_language': config.response_language,

                        'default_cli_provider': config.default_cli_provider
                    },
                    'metadata': {
                        'created_by': config.created_by,
                        'created_at': config.created_at,
                        'updated_by': config.updated_by,
                        'updated_at': config.updated_at,
                        'update_count': config.update_count
                    }
                }
                all_configs.append(config_dict)
            
            # Apply filters
            session_type = request.args.get('session_type')
            search = request.args.get('search')
            
            filtered_configs = all_configs
            
            if session_type:
                filtered_configs = [
                    c for c in filtered_configs 
                    if c.get('session_type') == session_type
                ]
            
            if search:
                filtered_configs = [
                    c for c in filtered_configs 
                    if search.lower() in c.get('session_id', '').lower()
                ]
            
            # Apply sorting
            sort_field = request.args.get('sort', 'updated_at')
            sort_order = request.args.get('order', 'desc')
            
            reverse = (sort_order == 'desc')
            
            try:
                filtered_configs.sort(
                    key=lambda x: x.get('metadata', {}).get(sort_field, ''),
                    reverse=reverse
                )
            except Exception as e:
                logger.warning(f"Sorting error: {e}")
            
            return jsonify({
                'success': True,
                'data': filtered_configs
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting configs: {e}", exc_info=True)
            log_api_error(
                endpoint='/api/configs',
                error=e,
                status_code=500,
                user='admin'
            )
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve configurations'
                }
            }), 500
    
    # Apply rate limit and register route
    get_configs = apply_rate_limit(auth_manager.require_auth(_get_configs), 'api')
    app.route('/api/configs', methods=['GET'])(get_configs)
    
    @app.route('/api/configs/<session_id>', methods=['GET'])
    @auth_manager.require_auth
    def get_config(session_id: str):
        """Get single session configuration
        
        Response:
            {
                "success": true,
                "data": {
                    "session_id": "ou_xxx",
                    "session_type": "user",
                    "config": {...},
                    "metadata": {...}
                }
            }
        """
        try:
            # Check if config exists
            if session_id not in config_manager.configs:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Configuration for session {session_id} not found'
                    }
                }), 404
            
            config = config_manager.configs[session_id]
            config_dict = {
                'session_id': config.session_id,
                'session_type': config.session_type,
                'config': {
                    'target_project_dir': config.target_project_dir,
                    'response_language': config.response_language,

                    'default_cli_provider': config.default_cli_provider
                },
                'metadata': {
                    'created_by': config.created_by,
                    'created_at': config.created_at,
                    'updated_by': config.updated_by,
                    'updated_at': config.updated_at,
                    'update_count': config.update_count
                }
            }
            
            return jsonify({
                'success': True,
                'data': config_dict
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting config for {session_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve configuration'
                }
            }), 500
    
    @app.route('/api/configs/<session_id>/effective', methods=['GET'])
    @auth_manager.require_auth
    def get_effective_config(session_id: str):
        """Get effective configuration (with defaults applied)
        
        Response:
            {
                "success": true,
                "data": {
                    "effective_config": {...}
                }
            }
        """
        try:
            # Determine session type (default to "user" if not found)
            session_type = "user"
            if session_id in config_manager.configs:
                session_type = config_manager.configs[session_id].session_type
            
            effective_config = config_manager.get_effective_config(
                session_id=session_id,
                session_type=session_type,
                temp_params=None
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'effective_config': effective_config
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting effective config for {session_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve effective configuration'
                }
            }), 500
    
    @app.route('/api/configs/global', methods=['GET'])
    @auth_manager.require_auth
    def get_global_config():
        """Get global default configuration
        
        Response:
            {
                "success": true,
                "data": {
                    "global_config": {...}
                }
            }
        """
        try:
            global_config = {}
            
            if config_manager.global_config:
                global_config = {
                    'target_project_dir': config_manager.global_config.target_directory or "",
                    'response_language': config_manager.global_config.response_language,
                    'default_cli_provider': config_manager.global_config.default_cli_provider,
                    'agent_enabled': config_manager.global_config.agent_enabled
                }
            else:
                # Return default values if no global config
                global_config = {
                    'target_project_dir': "",
                    'response_language': None,
                    'default_cli_provider': None,
                    'agent_enabled': True
                }
            
            return jsonify({
                'success': True,
                'data': {
                    'global_config': global_config
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting global config: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve global configuration'
                }
            }), 500
    
    @app.route('/api/configs/global', methods=['PUT'])
    @auth_manager.require_auth
    def update_global_config():
        """Update global default configuration
        
        Request body:
            {
                "target_project_dir": "/path/to/project",
                "response_language": "zh-CN",
                "default_cli_provider": "gemini"
            }
        
        Response:
            {
                "success": true,
                "data": {
                    "global_config": {...}
                },
                "message": "Global configuration updated successfully"
            }
        """
        try:
            import os
            from pathlib import Path
            
            data = request.get_json()
            
            # Validate provider values
            if 'default_cli_provider' in data:
                cli_provider = data['default_cli_provider'] if data['default_cli_provider'] else None
                if cli_provider and cli_provider not in config_manager.VALID_PROVIDERS:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_PROVIDER',
                            'message': f'Invalid CLI provider. Must be one of: {config_manager.VALID_PROVIDERS}',
                            'field': 'default_cli_provider'
                        }
                    }), 400
            
            # Validate layer values
            
            env_path = Path('.env')
            if not env_path.exists():
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'ENV_FILE_NOT_FOUND',
                        'message': '.env file not found'
                    }
                }), 404
            
            # Read .env file
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
            
            # Update .env file
            updated_lines = []
            updated_keys = set()
            
            for line in env_lines:
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    updated_lines.append(line)
                    continue
                
                # Parse key=value
                if '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    
                    # Update matching keys
                    if key == 'TARGET_PROJECT_DIR' and 'target_project_dir' in data:
                        value = data['target_project_dir'] or ''
                        updated_lines.append(f'{key}={value}\n')
                        updated_keys.add('target_project_dir')
                    elif key == 'RESPONSE_LANGUAGE' and 'response_language' in data:
                        value = data['response_language'] or ''
                        updated_lines.append(f'{key}={value}\n')
                        updated_keys.add('response_language')
                    elif key == 'DEFAULT_CLI_PROVIDER' and 'default_cli_provider' in data:
                        value = data['default_cli_provider'] or ''
                        updated_lines.append(f'{key}={value}\n')
                        updated_keys.add('default_cli_provider')
                    elif key == 'AGENT_ENABLED' and 'agent_enabled' in data:
                        value = 'true' if data['agent_enabled'] else 'false'
                        updated_lines.append(f'{key}={value}\n')
                        updated_keys.add('agent_enabled')
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Write updated .env file
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            # Update global_config object in memory
            if config_manager.global_config:
                if 'target_project_dir' in data:
                    config_manager.global_config.target_directory = data['target_project_dir'] or None
                if 'response_language' in data:
                    config_manager.global_config.response_language = data['response_language'] or None
                if 'agent_enabled' in data:
                    config_manager.global_config.agent_enabled = data['agent_enabled']
            
            if 'default_cli_provider' in data:
                cli_provider = data['default_cli_provider'] if data['default_cli_provider'] else None
                if cli_provider and cli_provider not in config_manager.VALID_PROVIDERS:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_PROVIDER',
                            'message': f'Invalid CLI provider. Must be one of: {config_manager.VALID_PROVIDERS}',
                            'field': 'default_cli_provider'
                        }
                    }), 400
            
            # Validate layer values
            
            # Log configuration change
            changes = {}
            if 'target_project_dir' in data:
                changes['target_project_dir'] = data['target_project_dir']
            if 'response_language' in data:
                changes['response_language'] = data['response_language']
            if 'default_cli_provider' in data:
                changes['default_cli_provider'] = data['default_cli_provider']
            if 'agent_enabled' in data:
                changes['agent_enabled'] = data['agent_enabled']
            
            # Return updated global configuration
            updated_global_config = {
                'target_project_dir': config_manager.global_config.target_directory or "",
                'response_language': config_manager.global_config.response_language,
                'default_cli_provider': config_manager.global_config.default_cli_provider,
                'agent_enabled': config_manager.global_config.agent_enabled
            }
            
            logger.info("Global configuration updated successfully")
            return jsonify({
                'success': True,
                'data': {
                    'global_config': updated_global_config
                },
                'message': 'Global configuration updated successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error updating config for {session_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update configuration'
                }
            }), 500
    
    @app.route('/api/configs/<session_id>', methods=['DELETE'])
    @auth_manager.require_auth
    def delete_config(session_id: str):
        """Delete session configuration (reset to defaults)
        
        Response:
            {
                "success": true,
                "message": "Configuration deleted successfully"
            }
        """
        try:
            success, msg = config_manager.reset_config(session_id)
            
            if success:
                logger.info(f"Configuration deleted for session {session_id}")
                log_config_change(
                    session_id=session_id,
                    action='delete',
                    user='admin'
                )
                return jsonify({
                    'success': True,
                    'message': 'Configuration deleted successfully'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': msg
                    }
                }), 404
            
        except Exception as e:
            logger.error(f"Error deleting config for {session_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete configuration'
                }
            }), 500
    
    # ==================== Export/Import Routes ====================
    
    def _export_configs():
        """Export all configurations as JSON file
        
        Response:
            JSON file download
        """
        try:
            import json
            import io
            from datetime import datetime
            
            # Collect all configuration data
            export_data = {
                'export_timestamp': datetime.utcnow().isoformat() + 'Z',
                'export_version': '1.0',
                'configs': []
            }
            
            # Add all session configurations
            for session_id, config in config_manager.configs.items():
                config_dict = {
                    'session_id': config.session_id,
                    'session_type': config.session_type,
                    'config': {
                        'target_project_dir': config.target_project_dir,
                        'response_language': config.response_language,

                        'default_cli_provider': config.default_cli_provider
                    },
                    'metadata': {
                        'created_by': config.created_by,
                        'created_at': config.created_at,
                        'updated_by': config.updated_by,
                        'updated_at': config.updated_at,
                        'update_count': config.update_count
                    }
                }
                export_data['configs'].append(config_dict)
            
            # Convert to JSON
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            
            # Create file-like object
            file_obj = io.BytesIO(json_bytes)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'feishu_bot_configs_{timestamp}.json'
            
            logger.info(f"Exporting {len(export_data['configs'])} configurations")
            
            # Return file download
            return send_file(
                file_obj,
                mimetype='application/json',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            logger.error(f"Error exporting configs: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to export configurations'
                }
            }), 500
    
    # Apply rate limit and register route
    export_configs = apply_rate_limit(auth_manager.require_auth(_export_configs), 'export_import')
    app.route('/api/configs/export', methods=['POST'])(export_configs)
    
    def _import_configs():
        """Import configurations from JSON file
        
        Request:
            multipart/form-data with 'file' field
        
        Response:
            {
                "success": true,
                "data": {
                    "imported_count": 5
                },
                "message": "Configurations imported successfully"
            }
        """
        try:
            import json
            import shutil
            from datetime import datetime
            from ...models import SessionConfig
            
            # Check if file is present in request
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_FILE',
                        'message': 'No file provided in request'
                    }
                }), 400
            
            file = request.files['file']
            
            # Check if file has a filename
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'EMPTY_FILENAME',
                        'message': 'No file selected'
                    }
                }), 400
            
            # Read and parse JSON file
            try:
                file_content = file.read().decode('utf-8')
                import_data = json.loads(file_content)
            except json.JSONDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_JSON',
                        'message': f'Invalid JSON format: {str(e)}'
                    }
                }), 400
            except UnicodeDecodeError as e:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_ENCODING',
                        'message': 'File must be UTF-8 encoded'
                    }
                }), 400
            
            # Validate JSON structure
            if not isinstance(import_data, dict):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_FORMAT',
                        'message': 'Import data must be a JSON object'
                    }
                }), 400
            
            if 'configs' not in import_data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_CONFIGS',
                        'message': 'Import data must contain "configs" field'
                    }
                }), 400
            
            configs_list = import_data['configs']
            if not isinstance(configs_list, list):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CONFIGS_FORMAT',
                        'message': '"configs" field must be an array'
                    }
                }), 400
            
            # Validate each configuration
            required_fields = ['session_id', 'session_type', 'config', 'metadata']
            required_config_fields = ['target_project_dir', 'response_language', 
                                     'default_cli_provider']
            required_metadata_fields = ['created_by', 'created_at', 'updated_by', 
                                       'updated_at', 'update_count']
            
            for idx, config_data in enumerate(configs_list):
                # Check required top-level fields
                missing_fields = [f for f in required_fields if f not in config_data]
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'MISSING_REQUIRED_FIELDS',
                            'message': f'Configuration at index {idx} is missing required fields: {missing_fields}'
                        }
                    }), 400
                
                # Check required config fields
                config_obj = config_data.get('config', {})
                missing_config_fields = [f for f in required_config_fields if f not in config_obj]
                if missing_config_fields:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'MISSING_CONFIG_FIELDS',
                            'message': f'Configuration at index {idx} is missing config fields: {missing_config_fields}'
                        }
                    }), 400
                
                # Check required metadata fields
                metadata_obj = config_data.get('metadata', {})
                missing_metadata_fields = [f for f in required_metadata_fields if f not in metadata_obj]
                if missing_metadata_fields:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'MISSING_METADATA_FIELDS',
                            'message': f'Configuration at index {idx} is missing metadata fields: {missing_metadata_fields}'
                        }
                    }), 400
                
                # Validate provider values
                cli_provider = config_obj.get('default_cli_provider')
                if cli_provider and cli_provider not in config_manager.VALID_PROVIDERS:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_CLI_PROVIDER',
                            'message': f'Configuration at index {idx} has invalid CLI provider: {cli_provider}'
                        }
                    }), 400
                
                # Validate layer values
                layer = config_obj.get()
                if layer and layer not in config_manager.VALID_LAYERS:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_LAYER',
                            'message': f'Configuration at index {idx} has invalid layer: {layer}'
                        }
                    }), 400
            
            # Create backup before importing
            import os
            if os.path.exists(config_manager.storage_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{config_manager.storage_path}.backup_{timestamp}"
                try:
                    shutil.copy2(config_manager.storage_path, backup_path)
                    logger.info(f"Created backup at {backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
                    # Continue with import even if backup fails
            
            # Import configurations
            imported_count = 0
            for config_data in configs_list:
                try:
                    session_id = config_data['session_id']
                    session_type = config_data['session_type']
                    config_obj = config_data['config']
                    metadata_obj = config_data['metadata']
                    
                    # Create SessionConfig object
                    session_config = SessionConfig(
                        session_id=session_id,
                        session_type=session_type,
                        target_project_dir=config_obj.get('target_project_dir'),
                        response_language=config_obj.get('response_language'),
                        default_cli_provider=config_obj.get('default_cli_provider'),
                        created_by=metadata_obj.get('created_by'),
                        created_at=metadata_obj.get('created_at'),
                        updated_by=metadata_obj.get('updated_by'),
                        updated_at=metadata_obj.get('updated_at'),
                        update_count=metadata_obj.get('update_count', 0)
                    )
                    
                    # Add to config manager
                    config_manager.configs[session_id] = session_config
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import config for session {config_data.get('session_id')}: {e}")
                    # Continue with other configs
            
            # Save all configurations
            config_manager.save_configs()
            
            logger.info(f"Successfully imported {imported_count} configurations")
            return jsonify({
                'success': True,
                'data': {
                    'imported_count': imported_count
                },
                'message': f'Successfully imported {imported_count} configuration(s)'
            }), 200
            
        except Exception as e:
            logger.error(f"Error importing configs: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to import configurations'
                }
            }), 500
    
    # Apply rate limit and register route
    import_configs = apply_rate_limit(auth_manager.require_auth(_import_configs), 'export_import')
    app.route('/api/configs/import', methods=['POST'])(import_configs)
    
    # ==================== Session History Routes ====================
    
    @app.route('/api/sessions', methods=['GET'])
    @auth_manager.require_auth
    def get_sessions():
        """Get all sessions (both active and archived)
        
        Query parameters:
            - user_id: Filter by user_id
            - search: Search by session_id or user_id
            - sort: Sort by field (default: last_active)
            - order: Sort order (asc/desc, default: desc)
            - page: Page number (default: 1)
            - page_size: Items per page (default: 20)
        
        Response:
            {
                "success": true,
                "data": {
                    "sessions": [...],
                    "total": 100,
                    "page": 1,
                    "page_size": 20
                }
            }
        """
        try:
            import os
            import json
            from pathlib import Path
            
            all_sessions = []
            
            # Read active sessions from sessions.json
            sessions_json_path = Path('data/sessions.json')
            if sessions_json_path.exists():
                try:
                    with open(sessions_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        sessions_data = data.get('sessions', {})
                        for user_id, session_dict in sessions_data.items():
                            # Extract summary info
                            message_count = len(session_dict.get('messages', []))
                            first_message = session_dict.get('messages', [{}])[0].get('content', '')[:100] if message_count > 0 else ''
                            
                            session_summary = {
                                'session_id': session_dict.get('session_id'),
                                'user_id': session_dict.get('user_id'),
                                'created_at': session_dict.get('created_at'),
                                'last_active': session_dict.get('last_active'),
                                'message_count': message_count,
                                'first_message': first_message,
                                'status': 'active'
                            }
                            all_sessions.append(session_summary)
                except Exception as e:
                    logger.warning(f"Failed to read sessions.json: {e}")
            
            # Read archived sessions from archived_sessions directory
            sessions_dir = Path('data/archived_sessions')
            if sessions_dir.exists():
                for session_file in sessions_dir.glob('*.json'):
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                            
                            # Extract summary info
                            message_count = len(session_data.get('messages', []))
                            first_message = session_data.get('messages', [{}])[0].get('content', '')[:100] if message_count > 0 else ''
                            
                            session_summary = {
                                'session_id': session_data.get('session_id'),
                                'user_id': session_data.get('user_id'),
                                'created_at': session_data.get('created_at'),
                                'last_active': session_data.get('last_active'),
                                'message_count': message_count,
                                'first_message': first_message,
                                'status': 'archived'
                            }
                            all_sessions.append(session_summary)
                    except Exception as e:
                        logger.warning(f"Failed to read session file {session_file}: {e}")
                        continue
            
            # Apply filters
            user_id = request.args.get('user_id')
            search = request.args.get('search')
            
            filtered_sessions = all_sessions
            
            if user_id:
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if s.get('user_id') == user_id
                ]
            
            if search:
                filtered_sessions = [
                    s for s in filtered_sessions 
                    if search.lower() in str(s.get('session_id', '')).lower() 
                    or search.lower() in str(s.get('user_id', '')).lower()
                ]
            
            # Apply sorting
            sort_field = request.args.get('sort', 'last_active')
            sort_order = request.args.get('order', 'desc')
            
            reverse = (sort_order == 'desc')
            
            try:
                filtered_sessions.sort(
                    key=lambda x: x.get(sort_field, 0),
                    reverse=reverse
                )
            except Exception as e:
                logger.warning(f"Sorting error: {e}")
            
            # Apply pagination
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 20))
            
            total = len(filtered_sessions)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            paginated_sessions = filtered_sessions[start_idx:end_idx]
            
            return jsonify({
                'success': True,
                'data': {
                    'sessions': paginated_sessions,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting sessions: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve sessions'
                }
            }), 500
    
    @app.route('/api/sessions/<session_id>', methods=['GET'])
    @auth_manager.require_auth
    def get_session(session_id: str):
        """Get single session detail
        
        Response:
            {
                "success": true,
                "data": {
                    "session_id": "xxx",
                    "user_id": "xxx",
                    "created_at": 1234567890,
                    "last_active": 1234567890,
                    "messages": [...],
                    "status": "active" or "archived"
                }
            }
        """
        try:
            import os
            import json
            from pathlib import Path
            
            session_data = None
            status = None
            
            # First check in active sessions (sessions.json)
            sessions_json_path = Path('data/sessions.json')
            if sessions_json_path.exists():
                try:
                    with open(sessions_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        sessions_data = data.get('sessions', {})
                        for user_id, session_dict in sessions_data.items():
                            if session_dict.get('session_id') == session_id:
                                session_data = session_dict
                                status = 'active'
                                break
                except Exception as e:
                    logger.warning(f"Failed to read sessions.json: {e}")
            
            # If not found in active sessions, check in archived sessions
            if not session_data:
                sessions_dir = Path('data/archived_sessions')
                if sessions_dir.exists():
                    for file in sessions_dir.glob(f'*_{session_id}_*.json'):
                        try:
                            with open(file, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                                status = 'archived'
                                break
                        except Exception as e:
                            logger.warning(f"Failed to read archived session file {file}: {e}")
            
            if not session_data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Session {session_id} not found'
                    }
                }), 404
            
            # Add status to session data
            session_data['status'] = status
            
            return jsonify({
                'success': True,
                'data': session_data
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve session'
                }
            }), 500
    
    @app.route('/api/sessions/<session_id>', methods=['DELETE'])
    @auth_manager.require_auth
    def delete_session(session_id: str):
        """Delete session
        
        Response:
            {
                "success": true,
                "message": "Session deleted successfully"
            }
        """
        try:
            import os
            from pathlib import Path
            
            # Get archived sessions directory
            sessions_dir = Path('data/archived_sessions')
            
            if not sessions_dir.exists():
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Session {session_id} not found'
                    }
                }), 404
            
            # Find and delete session file
            session_file = None
            for file in sessions_dir.glob(f'*_{session_id}_*.json'):
                session_file = file
                break
            
            if not session_file:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Session {session_id} not found'
                    }
                }), 404
            
            # Delete file
            os.remove(session_file)
            
            logger.info(f"Session {session_id} deleted successfully")
            return jsonify({
                'success': True,
                'message': 'Session deleted successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete session'
                }
            }), 500
    
    # ==================== Tool Management Routes ====================
    
    @app.route('/api/tools', methods=['GET'])
    @auth_manager.require_auth
    def get_tools():
        """Get all tools with their enabled status

        Dynamically loads tools from the agents.tools module.

        Response:
            {
                "success": true,
                "data": [
                    {
                        "name": "execute_shell_command",
                        "description": "Execute shell commands",
                        "enabled": true
                    }
                ]
            }
        """
        try:
            # Dynamically load tools from the tools module using relative import
            from ...agents.tools import __all__ as tool_names
            from ...agents import tools as tools_module

            tools = []
            for tool_name in tool_names:
                try:
                    # Get the tool function from the module
                    tool_func = getattr(tools_module, tool_name, None)

                    # Get description from docstring
                    description = "No description available"
                    if tool_func and hasattr(tool_func, '__doc__') and tool_func.__doc__:
                        # Extract first line of docstring as description
                        doc_lines = tool_func.__doc__.strip().split('\n')
                        if doc_lines:
                            description = doc_lines[0].strip()

                    tools.append({
                        "name": tool_name,
                        "description": description,
                        "enabled": tool_state_manager.get_tool_state(tool_name) if tool_state_manager else True
                    })
                except Exception as e:
                    logger.warning(f"Failed to load tool {tool_name}: {e}")
                    # Still add the tool with default description
                    tools.append({
                        "name": tool_name,
                        "description": f"Tool: {tool_name}",
                        "enabled": tool_state_manager.get_tool_state(tool_name) if tool_state_manager else True
                    })

            return jsonify({
                'success': True,
                'data': tools
            }), 200

        except Exception as e:
            logger.error(f"Error getting tools: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': f'Failed to retrieve tools: {str(e)}'
                }
            }), 500
    
    @app.route('/api/tools/<name>/toggle', methods=['POST'])
    @auth_manager.require_auth
    def toggle_tool(name):
        """Toggle tool enabled status
        
        Response:
            {
                "success": true,
                "data": {
                    "name": "execute_shell_command",
                    "enabled": false
                }
            }
        """
        try:
            if tool_state_manager:
                new_state = tool_state_manager.toggle_tool_state(name)
                return jsonify({
                    'success': True,
                    'data': {
                        'name': name,
                        'enabled': new_state
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': 'Tool state manager not available'
                    }
                }), 500
            
        except Exception as e:
            logger.error(f"Error toggling tool: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to toggle tool'
                }
            }), 500
    
    @app.route('/api/tools/enable-all', methods=['POST'])
    @auth_manager.require_auth
    def enable_all_tools():
        """Enable all tools
        
        Response:
            {
                "success": true,
                "message": "All tools enabled"
            }
        """
        try:
            if tool_state_manager:
                tool_state_manager.enable_all_tools()
                return jsonify({
                    'success': True,
                    'message': 'All tools enabled'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': 'Tool state manager not available'
                    }
                }), 500
            
        except Exception as e:
            logger.error(f"Error enabling all tools: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to enable all tools'
                }
            }), 500
    
    @app.route('/api/tools/disable-all', methods=['POST'])
    @auth_manager.require_auth
    def disable_all_tools():
        """Disable all tools
        
        Response:
            {
                "success": true,
                "message": "All tools disabled"
            }
        """
        try:
            if tool_state_manager:
                tool_state_manager.disable_all_tools()
                return jsonify({
                    'success': True,
                    'message': 'All tools disabled'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INTERNAL_ERROR',
                        'message': 'Tool state manager not available'
                    }
                }), 500
            
        except Exception as e:
            logger.error(f"Error disabling all tools: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to disable all tools'
                }
            }), 500
    
    logger.info("API routes registered successfully")

"""
Provider Configuration API Routes Module

This module defines RESTful API endpoints for managing AI provider configurations.
Provides endpoints for CRUD operations on provider configs and default provider management.
"""

import logging
from flask import Flask, request, jsonify
from typing import Dict, Any

from ...core.provider_config_manager import ProviderConfigManager
from ...models import ProviderConfig
from ..auth import AuthManager
from ..logging_config import log_config_change

logger = logging.getLogger(__name__)


def register_provider_api_routes(
    app: Flask,
    provider_config_manager: ProviderConfigManager,
    auth_manager: AuthManager,
    rate_limits: dict = None
):
    """Register provider configuration API routes with the Flask app
    
    Args:
        app: Flask application instance
        provider_config_manager: Provider configuration manager instance
        auth_manager: Authentication manager instance
        rate_limits: Dictionary of rate limit decorators (optional)
    """
    
    # Helper function to apply rate limit if available
    def apply_rate_limit(route_func, limit_type):
        """Apply rate limit decorator if available"""
        if rate_limits and limit_type in rate_limits:
            return rate_limits[limit_type](route_func)
        return route_func
    
    # ==================== Provider Configuration Routes ====================
    
    def _get_providers():
        """Get all provider configurations
        
        Response:
            {
                "success": true,
                "data": [
                    {
                        "name": "openai-gpt4",
                        "type": "openai_compatible",
                        "base_url": "https://api.openai.com/v1",
                        "api_key": "sk-****",
                        "model": "gpt-4",
                        "is_default": true,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        """
        try:
            # Get all configurations (with api_key masked)
            configs = provider_config_manager.list_configs()
            safe_configs = [config.to_safe_dict() for config in configs]
            
            return jsonify({
                'success': True,
                'data': safe_configs
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting providers: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve provider configurations'
                }
            }), 500
    
    # Apply rate limit and register route
    get_providers = apply_rate_limit(auth_manager.require_auth(_get_providers), 'api')
    app.route('/api/providers', methods=['GET'])(get_providers)
    
    @app.route('/api/providers', methods=['POST'])
    @auth_manager.require_auth
    def create_provider():
        """Create new provider configuration
        
        Request body:
            {
                "name": "openai-gpt4",
                "type": "openai_compatible",
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-...",
                "model": "gpt-4"
            }
        
        Response:
            {
                "success": true,
                "data": {
                    "name": "openai-gpt4",
                    ...
                },
                "message": "Provider configuration created successfully"
            }
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['name', 'type', 'api_key', 'models']
            missing_fields = [f for f in required_fields if not data.get(f)]
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELDS',
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }
                }), 400
            
            # Validate models field
            if not isinstance(data['models'], list) or len(data['models']) == 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_MODELS',
                        'message': 'models must be a non-empty array'
                    }
                }), 400
            
            # Validate default_model - auto-set to first model if not provided
            default_model = data.get('default_model') or data['models'][0]
            if default_model not in data['models']:
                default_model = data['models'][0]
            
            # Validate type
            valid_types = ['openai_compatible', 'claude_compatible', 'gemini_compatible']
            if data['type'] not in valid_types:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TYPE',
                        'message': f'Invalid type. Must be one of: {", ".join(valid_types)}'
                    }
                }), 400
            
            # Create ProviderConfig object
            config = ProviderConfig(
                name=data['name'],
                type=data['type'],
                base_url=data.get('base_url', ''),
                api_key=data['api_key'],
                models=data['models'],
                default_model=default_model,
                is_default=False
            )
            
            # Add configuration
            success, message = provider_config_manager.add_config(config)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'ADD_FAILED',
                        'message': message
                    }
                }), 400
            
            # Log configuration change
            log_config_change(
                session_id=f'provider:{config.name}',
                action='create',
                user='admin',
                changes=config.to_safe_dict()
            )
            
            logger.info(f"Provider configuration created: {config.name}")
            return jsonify({
                'success': True,
                'data': config.to_safe_dict(),
                'message': 'Provider configuration created successfully'
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating provider: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create provider configuration'
                }
            }), 500
    
    @app.route('/api/providers/<name>', methods=['GET'])
    @auth_manager.require_auth
    def get_provider(name: str):
        """Get single provider configuration
        
        Response:
            {
                "success": true,
                "data": {
                    "name": "openai-gpt4",
                    ...
                }
            }
        """
        try:
            config = provider_config_manager.get_config(name)
            
            if not config:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Provider configuration "{name}" not found'
                    }
                }), 404
            
            return jsonify({
                'success': True,
                'data': config.to_safe_dict()
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting provider {name}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve provider configuration'
                }
            }), 500
    
    @app.route('/api/providers/<name>', methods=['PUT'])
    @auth_manager.require_auth
    def update_provider(name: str):
        """Update provider configuration
        
        Request body:
            {
                "name": "openai-gpt4-updated",
                "type": "openai_compatible",
                "base_url": "https://api.openai.com/v1",
                "api_key": "sk-...",
                "model": "gpt-4-turbo"
            }
        
        Response:
            {
                "success": true,
                "data": {
                    "name": "openai-gpt4-updated",
                    ...
                },
                "message": "Provider configuration updated successfully"
            }
        """
        try:
            data = request.get_json()
            
            # Check if config exists
            existing_config = provider_config_manager.get_config(name)
            if not existing_config:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Provider configuration "{name}" not found'
                    }
                }), 404
            
            # Validate required fields
            required_fields = ['name', 'type', 'models']
            missing_fields = [f for f in required_fields if not data.get(f)]
            
            if missing_fields:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELDS',
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }
                }), 400
            
            # Validate models field
            if not isinstance(data['models'], list) or len(data['models']) == 0:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_MODELS',
                        'message': 'models must be a non-empty array'
                    }
                }), 400
            
            # Validate default_model - auto-set to first model if not provided
            default_model = data.get('default_model') or data['models'][0]
            if default_model not in data['models']:
                default_model = data['models'][0]
            
            # Validate type
            valid_types = ['openai_compatible', 'claude_compatible', 'gemini_compatible']
            if data['type'] not in valid_types:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_TYPE',
                        'message': f'Invalid type. Must be one of: {", ".join(valid_types)}'
                    }
                }), 400
            
            # Use existing api_key if not provided (editing without changing key)
            api_key = data.get('api_key') or existing_config.api_key
            
            # Create updated ProviderConfig object
            updated_config = ProviderConfig(
                name=data['name'],
                type=data['type'],
                base_url=data.get('base_url', ''),
                api_key=api_key,
                models=data['models'],
                default_model=default_model,
                is_default=existing_config.is_default  # Preserve default status
            )
            
            # Update configuration
            success, message = provider_config_manager.update_config(name, updated_config)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'UPDATE_FAILED',
                        'message': message
                    }
                }), 400
            
            # Log configuration change
            log_config_change(
                session_id=f'provider:{updated_config.name}',
                action='update',
                user='admin',
                changes=updated_config.to_safe_dict()
            )
            
            logger.info(f"Provider configuration updated: {name} -> {updated_config.name}")
            return jsonify({
                'success': True,
                'data': updated_config.to_safe_dict(),
                'message': 'Provider configuration updated successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error updating provider {name}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update provider configuration'
                }
            }), 500
    
    @app.route('/api/providers/<name>', methods=['DELETE'])
    @auth_manager.require_auth
    def delete_provider(name: str):
        """Delete provider configuration
        
        Response:
            {
                "success": true,
                "message": "Provider configuration deleted successfully"
            }
        """
        try:
            success, message = provider_config_manager.delete_config(name)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'DELETE_FAILED',
                        'message': message
                    }
                }), 404 if 'not found' in message.lower() else 400
            
            # Log configuration change
            log_config_change(
                session_id=f'provider:{name}',
                action='delete',
                user='admin'
            )
            
            logger.info(f"Provider configuration deleted: {name}")
            return jsonify({
                'success': True,
                'message': 'Provider configuration deleted successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error deleting provider {name}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete provider configuration'
                }
            }), 500
    
    @app.route('/api/providers/<name>/set-default', methods=['POST'])
    @auth_manager.require_auth
    def set_default_provider(name: str):
        """Set provider as default
        
        Response:
            {
                "success": true,
                "message": "Provider set as default successfully"
            }
        """
        try:
            success, message = provider_config_manager.set_default(name)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'SET_DEFAULT_FAILED',
                        'message': message
                    }
                }), 404 if 'not found' in message.lower() else 400
            
            # Log configuration change
            log_config_change(
                session_id=f'provider:{name}',
                action='set_default',
                user='admin'
            )
            
            logger.info(f"Provider set as default: {name}")
            return jsonify({
                'success': True,
                'message': message
            }), 200
            
        except Exception as e:
            logger.error(f"Error setting default provider {name}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to set default provider'
                }
            }), 500
    
    @app.route('/api/providers/default', methods=['GET'])
    @auth_manager.require_auth
    def get_default_provider():
        """Get current default provider
        
        Response:
            {
                "success": true,
                "data": {
                    "name": "openai-gpt4",
                    ...
                }
            }
        """
        try:
            config = provider_config_manager.get_default()
            
            if not config:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NO_DEFAULT',
                        'message': 'No default provider configured'
                    }
                }), 404
            
            return jsonify({
                'success': True,
                'data': config.to_safe_dict()
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting default provider: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to retrieve default provider'
                }
            }), 500
    
    @app.route('/api/providers/<name>/test', methods=['POST'])
    @auth_manager.require_auth
    def test_provider(name: str):
        """Test provider connection and model availability
        
        Uses industry best practices for LLM API testing:
        - Simple test prompt: "Hi" (minimal tokens)
        - Reasonable timeout (30 seconds)
        - Validates response format
        - Provides detailed error information
        
        Response:
            {
                "success": true,
                "message": "Provider test successful",
                "details": {
                    "provider": "openai-gpt4",
                    "model": "gpt-4",
                    "response_time_ms": 1234,
                    "response_length": 10
                }
            }
        """
        try:
            import time
            
            # Get provider config
            config = provider_config_manager.get_config(name)
            if not config:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'Provider configuration "{name}" not found'
                    }
                }), 404
            
            # Validate required fields
            if not config.api_key:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CONFIG',
                        'message': 'API key is missing'
                    }
                }), 400
            
            # Use model from request body, fallback to first available model
            body = request.get_json() or {}
            test_model = body.get('model') or (config.models[0] if config.models else None)
            
            if not test_model:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CONFIG',
                        'message': '没有可用的模型'
                    }
                }), 400
            
            # Test based on provider type
            start_time = time.time()
            
            try:
                if config.type == "openai_compatible":
                    # Test OpenAI-compatible API
                    from openai import OpenAI
                    
                    client = OpenAI(
                        api_key=config.api_key,
                        base_url=config.base_url if config.base_url else None,
                        timeout=30.0
                    )
                    
                    response = client.chat.completions.create(
                        model=test_model,
                        messages=[{"role": "user", "content": "Hi"}],
                        max_tokens=5
                    )
                    
                    response_text = response.choices[0].message.content
                    
                elif config.type == "claude_compatible":
                    # Test Claude-compatible API
                    import anthropic
                    
                    client = anthropic.Anthropic(
                        api_key=config.api_key,
                        base_url=config.base_url if config.base_url else None,
                        timeout=30.0
                    )
                    
                    response = client.messages.create(
                        model=test_model,
                        max_tokens=5,
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                    
                    response_text = response.content[0].text
                    
                elif config.type == "gemini_compatible":
                    # Test Gemini-compatible API
                    import google.generativeai as genai
                    
                    genai.configure(api_key=config.api_key)
                    model = genai.GenerativeModel(test_model)
                    
                    response = model.generate_content(
                        "Hi",
                        generation_config=genai.types.GenerationConfig(
                            max_output_tokens=5
                        )
                    )
                    
                    response_text = response.text
                    
                else:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'UNSUPPORTED_TYPE',
                            'message': f'Unsupported provider type: {config.type}'
                        }
                    }), 400
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                # Validate response
                if not response_text or not isinstance(response_text, str):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_RESPONSE',
                            'message': 'API returned invalid response format'
                        }
                    }), 400
                
                # Success response with detailed metrics
                return jsonify({
                    'success': True,
                    'message': f'✓ 连接成功 ({response_time_ms}ms)',
                    'details': {
                        'provider': name,
                        'type': config.type,
                        'model': test_model,
                        'response_time_ms': response_time_ms,
                        'response_length': len(response_text),
                        'status': 'healthy'
                    }
                }), 200
                
            except Exception as api_error:
                response_time_ms = int((time.time() - start_time) * 1000)
                error_msg = str(api_error)
                
                # Provide user-friendly error messages
                if 'timeout' in error_msg.lower():
                    user_message = '请求超时，请检查网络连接或 Base URL 配置'
                elif 'unauthorized' in error_msg.lower() or '401' in error_msg:
                    user_message = 'API Key 无效或已过期'
                elif 'not found' in error_msg.lower() or '404' in error_msg:
                    user_message = 'Base URL 或模型不存在，请检查配置'
                elif 'rate limit' in error_msg.lower() or '429' in error_msg:
                    user_message = 'API 调用频率超限，请稍后重试'
                elif 'invalid' in error_msg.lower() or '400' in error_msg:
                    user_message = '请求参数无效，请检查配置'
                else:
                    user_message = f'API 调用失败: {error_msg}'
                
                logger.error(f"Provider test failed for {name}: {api_error}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'TEST_FAILED',
                        'message': user_message,
                        'details': {
                            'provider': name,
                            'model': test_model,
                            'response_time_ms': response_time_ms,
                            'raw_error': error_msg
                        }
                    }
                }), 400
            
        except Exception as e:
            logger.error(f"Error testing provider {name}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': f'测试过程发生错误: {str(e)}'
                }
            }), 500
    
    logger.info("Provider API routes registered successfully")

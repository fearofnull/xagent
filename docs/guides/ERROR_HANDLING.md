# Web Admin Error Handling Guide

This document describes the unified error handling system for the Web Admin Interface.

## Overview

The error handling system provides:
- **Consistent error response format** across all API endpoints
- **Custom exception classes** for different error types
- **Error handling decorator** to automatically catch and format errors
- **HTTP status code mapping** for proper REST API responses

## Error Response Format

All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "field": "field_name"  // Optional, for field-specific errors
  }
}
```

## Custom Exception Classes

### WebAdminError (Base Class)
Base exception for all web admin errors.

```python
from xagent.web_admin.errors import WebAdminError

raise WebAdminError(
    message="Something went wrong",
    code="CUSTOM_ERROR",
    status_code=500,
    field="optional_field"
)
```

### ValidationError (400 Bad Request)
For validation and input errors.

```python
from xagent.web_admin.errors import ValidationError

raise ValidationError("Invalid email format", field="email")
```

### AuthenticationError (401 Unauthorized)
For authentication failures.

```python
from xagent.web_admin.errors import AuthenticationError

raise AuthenticationError("Invalid credentials")
```

### NotFoundError (404 Not Found)
For resource not found errors.

```python
from xagent.web_admin.errors import NotFoundError

raise NotFoundError("Configuration not found", resource_type="Configuration")
```

### InternalError (500 Internal Server Error)
For internal server errors.

```python
from xagent.web_admin.errors import InternalError

raise InternalError("Database connection failed")
```

## Using the Error Handling Decorator

The `@handle_errors` decorator automatically catches exceptions and returns properly formatted error responses.

### Basic Usage

```python
from flask import Flask, jsonify
from xagent.web_admin.errors import handle_errors, ValidationError

app = Flask(__name__)

@app.route('/api/example', methods=['POST'])
@handle_errors
def example_endpoint():
    data = request.get_json()
    
    # Validation
    if not data.get('name'):
        raise ValidationError("Name is required", field="name")
    
    # Your logic here
    result = process_data(data)
    
    return jsonify({
        'success': True,
        'data': result,
        'message': 'Operation successful'
    }), 200
```

### What the Decorator Handles

The decorator automatically catches and formats:

1. **WebAdminError and subclasses** - Returns with the specified status code
2. **ValueError** - Treated as validation error (400)
3. **KeyError** - Treated as missing field error (400)
4. **Generic Exception** - Treated as internal error (500)

### Example: Automatic Error Handling

```python
@app.route('/api/configs/<session_id>', methods=['GET'])
@handle_errors
def get_config(session_id: str):
    # If config doesn't exist, raise NotFoundError
    if session_id not in config_manager.configs:
        raise NotFoundError(f"Configuration for session {session_id} not found")
    
    # If something unexpected happens, it's automatically caught
    config = config_manager.configs[session_id]
    
    return jsonify({
        'success': True,
        'data': config.to_dict()
    }), 200
```

## HTTP Status Code Mapping

The system provides a comprehensive mapping of error codes to HTTP status codes:

### Authentication Errors (401)
- `AUTHENTICATION_ERROR`
- `INVALID_CREDENTIALS`
- `INVALID_TOKEN`
- `TOKEN_EXPIRED`

### Validation Errors (400)
- `VALIDATION_ERROR`
- `MISSING_FIELD`
- `MISSING_PASSWORD`
- `INVALID_PROVIDER`
- `INVALID_LAYER`
- `INVALID_JSON`
- `INVALID_FORMAT`

### Not Found Errors (404)
- `NOT_FOUND`
- `CONFIG_NOT_FOUND`

### Internal Errors (500)
- `INTERNAL_ERROR`
- `FILE_ERROR`
- `DATABASE_ERROR`

### Using Status Code Mapping

```python
from xagent.web_admin.errors import get_status_code_for_error

error_code = "VALIDATION_ERROR"
status_code = get_status_code_for_error(error_code)  # Returns 400
```

## Helper Functions

### format_error_response()
Manually format an error response.

```python
from xagent.web_admin.errors import format_error_response

error = ValueError("Invalid input")
response, status_code = format_error_response(
    error,
    status_code=400,
    code="VALIDATION_ERROR",
    field="username"
)
```

### format_success_response()
Format a success response.

```python
from xagent.web_admin.errors import format_success_response

response = format_success_response(
    data={'id': 1, 'name': 'Test'},
    message="Configuration updated successfully"
)
```

## Best Practices

### 1. Use Specific Exception Classes
```python
# Good
raise ValidationError("Invalid provider", field="default_provider")

# Avoid
raise Exception("Invalid provider")
```

### 2. Provide User-Friendly Messages
```python
# Good
raise NotFoundError("Configuration for session 'ou_123' not found")

# Avoid
raise NotFoundError("Config not in dict")
```

### 3. Include Field Names for Validation Errors
```python
# Good
raise ValidationError("Email format is invalid", field="email")

# Avoid
raise ValidationError("Email format is invalid")
```

### 4. Log Errors Appropriately
```python
import logging

logger = logging.getLogger(__name__)

@handle_errors
def my_endpoint():
    try:
        # Your logic
        pass
    except SomeSpecificError as e:
        logger.warning(f"Expected error occurred: {e}")
        raise ValidationError(str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise InternalError("An unexpected error occurred")
```

### 5. Don't Expose Internal Details
```python
# Good
raise InternalError("Failed to save configuration")

# Avoid
raise InternalError(f"Database error: {db_connection_string} - {error_details}")
```

## Testing Error Handling

### Testing Custom Exceptions
```python
def test_validation_error():
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Invalid input", field="username")
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.field == "username"
```

### Testing Decorated Endpoints
```python
def test_endpoint_error_handling(client):
    response = client.post('/api/endpoint', json={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data
    assert data['error']['code'] == 'VALIDATION_ERROR'
```

## Migration Guide

If you have existing endpoints without the error handling decorator:

### Before
```python
@app.route('/api/configs', methods=['GET'])
def get_configs():
    try:
        configs = config_manager.get_all_configs()
        return jsonify({
            'success': True,
            'data': configs
        }), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({
            'success': False,
            'error': {'message': str(e)}
        }), 500
```

### After
```python
@app.route('/api/configs', methods=['GET'])
@handle_errors
def get_configs():
    configs = config_manager.get_all_configs()
    return jsonify({
        'success': True,
        'data': configs
    }), 200
```

The decorator handles all error cases automatically!

## Summary

The unified error handling system provides:
- ✅ Consistent error response format
- ✅ Automatic exception handling with `@handle_errors`
- ✅ Proper HTTP status codes
- ✅ User-friendly error messages
- ✅ Field-specific error information
- ✅ Comprehensive logging

Use the decorator on all API endpoints to ensure consistent error handling across the entire web admin interface.

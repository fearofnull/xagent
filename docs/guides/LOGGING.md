# Web Admin Logging Guide

This document describes the comprehensive logging system for the Web Admin Interface.

## Overview

The logging system provides:
- **Structured log format** with timestamps, levels, and module names
- **Multiple log files** for different purposes (application, errors, access, authentication)
- **Rotating file handlers** to prevent disk space issues
- **Request/response logging** for all API calls
- **Authentication attempt logging** for security monitoring
- **Configuration change audit trail** for tracking modifications

## Log Files

All log files are stored in the `logs/` directory by default (configurable).

### 1. Application Log (`web_admin.log`)
General application logs including:
- Server startup/shutdown
- Configuration loading
- General information messages
- Warnings

**Rotation**: 10 MB per file, keeps 5 backups

### 2. Error Log (`web_admin_error.log`)
Error-level logs only:
- Exceptions and stack traces
- Critical errors
- Internal server errors

**Rotation**: 10 MB per file, keeps 5 backups

### 3. Access Log (`web_admin_access.log`)
HTTP request/response logs:
- Request method and path
- Client IP address
- Response status code
- Request duration
- Request body (with sensitive data masked)

**Rotation**: 10 MB per file, keeps 5 backups

### 4. Authentication Log (`web_admin_auth.log`)
Authentication-related events:
- Login attempts (successful and failed)
- Logout events
- Token validation failures
- IP addresses of authentication attempts

**Rotation**: 10 MB per file, keeps 5 backups

## Log Format

All logs use a consistent format:

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [module.name] message
```

Example:
```
[2024-01-15 14:30:45] [INFO] [web_admin.access] Request started: GET /api/configs from 192.168.1.100
[2024-01-15 14:30:45] [INFO] [web_admin.access] Request completed: GET /api/configs status=200 duration=0.123s
[2024-01-15 14:30:50] [WARNING] [web_admin.auth] Authentication failed: user=admin ip=192.168.1.100 reason=Invalid password
[2024-01-15 14:31:00] [ERROR] [web_admin.api] API error in /api/configs/ou_123: ValueError: Invalid provider (status=400, user=admin)
```

## Log Levels

The system supports standard Python logging levels:

- **DEBUG**: Detailed diagnostic information (request bodies, internal state)
- **INFO**: General informational messages (requests, successful operations)
- **WARNING**: Warning messages (failed auth attempts, validation errors)
- **ERROR**: Error messages (exceptions, failures)
- **CRITICAL**: Critical errors (system failures)

Default level: **INFO**

## Configuration

### Command-Line Options

```bash
python -m xagent.web_admin.server \
  --log-level INFO \
  --log-dir /path/to/logs
```

Options:
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-dir`: Directory for log files (default: ./logs)

### Programmatic Configuration

```python
from xagent.web_admin.server import WebAdminServer
from xagent.core.config_manager import ConfigManager

config_manager = ConfigManager()

server = WebAdminServer(
    config_manager=config_manager,
    host="0.0.0.0",
    port=5000,
    log_level="DEBUG",  # Set log level
    log_dir="/var/log/xagent"  # Custom log directory
)

server.start()
```

## Logging Features

### 1. Request Logging

All API requests are automatically logged with:
- Request start time
- HTTP method and path
- Client IP address
- Request body (with password fields masked)
- Response status code
- Request duration

Example:
```
[2024-01-15 14:30:45] [INFO] [web_admin.access] Request started: POST /api/auth/login from 192.168.1.100
[2024-01-15 14:30:45] [DEBUG] [web_admin.access] Request body: {'password': '***'}
[2024-01-15 14:30:45] [INFO] [web_admin.access] Request completed: POST /api/auth/login status=200 duration=0.050s
```

### 2. Authentication Logging

All authentication attempts are logged:

**Successful login:**
```
[2024-01-15 14:30:45] [INFO] [web_admin.auth] Authentication successful: user=admin ip=192.168.1.100
```

**Failed login:**
```
[2024-01-15 14:30:50] [WARNING] [web_admin.auth] Authentication failed: user=admin ip=192.168.1.100 reason=Invalid password
```

### 3. Configuration Change Logging

All configuration modifications are logged for audit purposes:

**Update:**
```
[2024-01-15 14:35:00] [INFO] [web_admin.config] Config update: session=ou_123 user=admin changes={'default_provider': 'claude', 'default_layer': 'api'}
```

**Delete:**
```
[2024-01-15 14:40:00] [INFO] [web_admin.config] Config delete: session=ou_123 user=admin
```

### 4. Error Logging

Errors are logged with full context:

```
[2024-01-15 14:45:00] [ERROR] [web_admin.api] API error in /api/configs/ou_123: ValueError: Invalid provider (status=400, user=admin)
Traceback (most recent call last):
  File "api_routes.py", line 123, in update_config
    validate_provider(data['provider'])
ValueError: Invalid provider
```

### 5. Sensitive Data Masking

The logging system automatically masks sensitive data:
- Password fields in request bodies are replaced with `***`
- JWT tokens are not logged
- Only error types and messages are logged, not full credentials

## Using the Logging System

### In Your Code

```python
from xagent.web_admin.logging_config import (
    get_logger,
    log_authentication_attempt,
    log_api_error,
    log_config_change
)

# Get a logger for your module
logger = get_logger(__name__)

# Log general messages
logger.info("Processing request")
logger.warning("Validation failed")
logger.error("Database error", exc_info=True)

# Log authentication attempts
log_authentication_attempt(
    success=True,
    username="admin",
    ip_address="192.168.1.100"
)

# Log API errors
try:
    process_request()
except Exception as e:
    log_api_error(
        endpoint="/api/configs",
        error=e,
        status_code=500,
        user="admin"
    )

# Log configuration changes
log_config_change(
    session_id="ou_123",
    action="update",
    user="admin",
    changes={"provider": "claude"}
)
```

## Log Rotation

All log files use rotating file handlers:
- **Max file size**: 10 MB
- **Backup count**: 5 files
- **Total max size**: ~50 MB per log type

When a log file reaches 10 MB:
1. Current file is renamed to `filename.log.1`
2. Previous backups are renamed (`.1` → `.2`, `.2` → `.3`, etc.)
3. Oldest backup (`.5`) is deleted
4. New `filename.log` is created

## Monitoring and Analysis

### View Recent Logs

```bash
# View last 50 lines of application log
tail -n 50 logs/web_admin.log

# Follow access log in real-time
tail -f logs/web_admin_access.log

# Search for errors
grep ERROR logs/web_admin_error.log

# Find failed authentication attempts
grep "Authentication failed" logs/web_admin_auth.log
```

### Log Analysis Examples

**Count requests by endpoint:**
```bash
grep "Request completed" logs/web_admin_access.log | \
  awk '{print $6}' | sort | uniq -c | sort -rn
```

**Find slow requests (>1 second):**
```bash
grep "Request completed" logs/web_admin_access.log | \
  awk '$NF > 1.0 {print}'
```

**Count failed login attempts by IP:**
```bash
grep "Authentication failed" logs/web_admin_auth.log | \
  awk -F'ip=' '{print $2}' | awk '{print $1}' | \
  sort | uniq -c | sort -rn
```

**Find all errors in the last hour:**
```bash
grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')" logs/web_admin_error.log
```

## Security Considerations

### What is Logged
- ✅ Request paths and methods
- ✅ Response status codes
- ✅ Client IP addresses
- ✅ Authentication attempts
- ✅ Configuration changes
- ✅ Error types and messages

### What is NOT Logged
- ❌ Passwords (masked as `***`)
- ❌ JWT tokens
- ❌ Full request bodies with sensitive data
- ❌ Database connection strings
- ❌ API keys or secrets

### Log File Security

Recommended file permissions:
```bash
# Application and access logs (readable by group)
chmod 640 logs/web_admin.log
chmod 640 logs/web_admin_access.log

# Error and auth logs (owner only)
chmod 600 logs/web_admin_error.log
chmod 600 logs/web_admin_auth.log

# Log directory
chmod 750 logs/
```

## Troubleshooting

### Logs Not Being Created

1. Check log directory permissions:
   ```bash
   ls -ld logs/
   ```

2. Check disk space:
   ```bash
   df -h
   ```

3. Verify log level is not too high:
   ```bash
   # Use DEBUG level to see all logs
   python -m xagent.web_admin.server --log-level DEBUG
   ```

### Log Files Growing Too Large

1. Reduce log level (INFO instead of DEBUG)
2. Adjust rotation settings in `logging_config.py`
3. Set up log archival/cleanup cron job

### Missing Request Logs

1. Ensure logging is configured before routes are registered
2. Check that `register_request_logging()` is called
3. Verify access logger is not disabled

## Best Practices

1. **Use appropriate log levels**
   - DEBUG: Development and troubleshooting
   - INFO: Production normal operations
   - WARNING: Potential issues
   - ERROR: Actual errors

2. **Include context in log messages**
   ```python
   # Good
   logger.info(f"Config updated for session {session_id} by {user}")
   
   # Avoid
   logger.info("Config updated")
   ```

3. **Use structured logging for important events**
   ```python
   # Use dedicated logging functions
   log_config_change(session_id, action, user, changes)
   
   # Instead of generic logging
   logger.info(f"Config changed: {session_id}")
   ```

4. **Log exceptions with stack traces**
   ```python
   try:
       risky_operation()
   except Exception as e:
       logger.error(f"Operation failed: {e}", exc_info=True)
   ```

5. **Don't log sensitive data**
   ```python
   # Good
   logger.info(f"User logged in: {username}")
   
   # Avoid
   logger.info(f"Login: {username} with password {password}")
   ```

## Summary

The Web Admin logging system provides:
- ✅ Comprehensive request/response logging
- ✅ Authentication attempt tracking
- ✅ Configuration change audit trail
- ✅ Error logging with stack traces
- ✅ Automatic log rotation
- ✅ Sensitive data masking
- ✅ Multiple log files for different purposes
- ✅ Configurable log levels and directories

All logs are automatically managed and rotated to prevent disk space issues while maintaining a complete audit trail of system activity.

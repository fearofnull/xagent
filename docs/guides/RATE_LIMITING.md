# Rate Limiting Documentation

## Overview

The Web Admin Interface implements rate limiting to prevent abuse and protect against brute force attacks. Rate limiting is implemented using Flask-Limiter with in-memory storage.

## Rate Limit Configuration

### Login Endpoint
- **Limit**: 5 requests per minute per IP address
- **Endpoint**: `POST /api/auth/login`
- **Purpose**: Prevent brute force password attacks
- **Error Message**: "Too many login attempts. Please try again later."

### API Endpoints
- **Limit**: 60 requests per minute per IP address
- **Endpoints**: All `/api/configs/*` endpoints (GET, PUT, DELETE)
- **Purpose**: Prevent API abuse and excessive resource usage
- **Error Message**: "API rate limit exceeded. Please slow down your requests."

### Export/Import Endpoints
- **Limit**: 10 requests per minute per IP address
- **Endpoints**: 
  - `POST /api/configs/export`
  - `POST /api/configs/import`
- **Purpose**: Prevent resource-intensive operations from overwhelming the server
- **Error Message**: "Export/import rate limit exceeded. Please wait before trying again."

## Rate Limit Headers

When rate limiting is enabled, the following headers are included in API responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time when the rate limit will reset (Unix timestamp)

## Rate Limit Exceeded Response

When a rate limit is exceeded, the API returns a 429 (Too Many Requests) status code with the following response format:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many login attempts. Please try again later."
  }
}
```

## Enabling/Disabling Rate Limiting

### Enable Rate Limiting (Default)

Rate limiting is enabled by default when starting the Web Admin Server:

```bash
python -m xagent.web_admin.server
```

### Disable Rate Limiting

To disable rate limiting (not recommended for production), use the `--disable-rate-limiting` flag:

```bash
python -m xagent.web_admin.server --disable-rate-limiting
```

### Programmatic Configuration

When creating a `WebAdminServer` instance programmatically:

```python
from xagent.web_admin.server import WebAdminServer
from xagent.core.config_manager import ConfigManager

config_manager = ConfigManager()

# Enable rate limiting (default)
server = WebAdminServer(
    config_manager=config_manager,
    enable_rate_limiting=True
)

# Disable rate limiting
server = WebAdminServer(
    config_manager=config_manager,
    enable_rate_limiting=False
)
```

## Rate Limiting Strategy

The rate limiter uses a **fixed-window** strategy:

- Requests are counted within fixed time windows (e.g., per minute)
- When the limit is reached, subsequent requests are rejected until the window resets
- Each IP address has its own independent rate limit counter

## Storage

Rate limit counters are stored in **memory** using Flask-Limiter's built-in memory storage:

- **Advantages**: Simple, no external dependencies, fast
- **Limitations**: 
  - Counters are reset when the server restarts
  - Not suitable for multi-instance deployments (each instance has its own counters)

For production deployments with multiple server instances, consider using Redis storage:

```python
from xagent.web_admin.rate_limiter import create_limiter

# In rate_limiter.py, modify create_limiter to use Redis:
limiter = Limiter(
    app=app,
    key_func=get_rate_limit_key,
    storage_uri="redis://localhost:6379",  # Redis storage
    strategy="fixed-window"
)
```

## Security Considerations

1. **Brute Force Protection**: The strict login rate limit (5/minute) makes brute force password attacks impractical
2. **API Abuse Prevention**: The API rate limit prevents excessive requests that could degrade performance
3. **Resource Protection**: The export/import rate limit protects against resource-intensive operations
4. **IP-Based Limiting**: Rate limits are applied per IP address, preventing a single client from overwhelming the server

## Monitoring

Rate limit violations are logged with WARNING level:

```
[2024-01-01 12:00:00] [WARNING] [xagent.web_admin.rate_limiter] Rate limit exceeded for 192.168.1.100 on /api/auth/login
```

Monitor these logs to identify potential attacks or misconfigured clients.

## Customizing Rate Limits

To customize rate limits, modify the `configure_rate_limits()` function in `xagent/web_admin/rate_limiter.py`:

```python
def configure_rate_limits(limiter: Limiter):
    # Custom login limit: 10 attempts per minute
    login_limit = limiter.limit(
        "10 per minute",
        error_message="Too many login attempts. Please try again later."
    )
    
    # Custom API limit: 120 requests per minute
    api_limit = limiter.limit(
        "120 per minute",
        error_message="API rate limit exceeded. Please slow down your requests."
    )
    
    # Custom export/import limit: 20 requests per minute
    export_import_limit = limiter.limit(
        "20 per minute",
        error_message="Export/import rate limit exceeded. Please wait before trying again."
    )
    
    return {
        'login': login_limit,
        'api': api_limit,
        'export_import': export_import_limit
    }
```

## Testing Rate Limits

To test rate limits manually:

1. **Test Login Rate Limit**:
   ```bash
   # Make 6 login attempts in quick succession
   for i in {1..6}; do
     curl -X POST http://localhost:5000/api/auth/login \
       -H "Content-Type: application/json" \
       -d '{"password":"wrong"}' \
       -w "\nStatus: %{http_code}\n"
   done
   ```
   The 6th request should return 429.

2. **Test API Rate Limit**:
   ```bash
   # Get a valid token first
   TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"password":"your_password"}' | jq -r '.data.token')
   
   # Make 61 API requests
   for i in {1..61}; do
     curl -X GET http://localhost:5000/api/configs \
       -H "Authorization: Bearer $TOKEN" \
       -w "\nStatus: %{http_code}\n"
   done
   ```
   The 61st request should return 429.

## Best Practices

1. **Production Deployment**: Always enable rate limiting in production environments
2. **Monitoring**: Monitor rate limit logs to identify potential attacks or issues
3. **Client Implementation**: Implement exponential backoff in clients when receiving 429 responses
4. **Load Balancing**: If using multiple server instances, consider Redis storage for consistent rate limiting
5. **Whitelist**: Consider implementing IP whitelisting for trusted clients that need higher limits

## Troubleshooting

### Rate Limits Too Strict

If legitimate users are hitting rate limits:

1. Increase the rate limits in `rate_limiter.py`
2. Consider implementing user-based rate limiting instead of IP-based
3. Implement a whitelist for trusted IPs

### Rate Limits Not Working

If rate limits are not being enforced:

1. Check that `enable_rate_limiting=True` when creating the server
2. Verify Flask-Limiter is installed: `pip install Flask-Limiter>=3.5.0`
3. Check logs for rate limiter initialization messages
4. Ensure decorators are applied correctly in `api_routes.py`

### Rate Limit Counters Reset Unexpectedly

If using in-memory storage, counters reset when the server restarts. For persistent counters, use Redis storage.

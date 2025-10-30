# Middleware Implementation Guide

## Overview

This document describes the middleware implementation for the Aztec List API, including request logging and CORS configuration.

## Architecture

The middleware follows the FastAPI/Starlette middleware pattern and integrates with the application's settings-based configuration system.

### Components

1. **Request Logging Middleware** (`app.core.middleware.RequestLoggingMiddleware`)
   - Tracks request/response lifecycle
   - Generates correlation IDs for request tracing
   - Logs performance metrics
   - Adds custom headers to responses

2. **CORS Middleware** (FastAPI built-in `CORSMiddleware`)
   - Handles cross-origin resource sharing
   - Configured via settings for different environments
   - Supports credential-based requests

## Configuration

### Settings Structure

Middleware configuration is managed through `app.core.settings.Settings`:

```python
# CORS Configuration
settings.cors.allowed_origins     # List of allowed frontend URLs
settings.cors.allow_credentials   # Enable cookies/auth headers
settings.cors.allowed_methods     # Allowed HTTP methods
settings.cors.allowed_headers     # Allowed request headers

# Logging Configuration
settings.logging.level           # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
settings.logging.format          # Log message format string
```

### Environment Variables

Configure via `.env` file using the nested delimiter pattern (`__`):

```bash
# CORS Settings
CORS__ALLOWED_ORIGINS='["http://localhost:3000", "http://localhost:5173"]'
CORS__ALLOW_CREDENTIALS=true
CORS__ALLOWED_METHODS='["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]'
CORS__ALLOWED_HEADERS='["*"]'

# Logging Settings
LOGGING__LEVEL="INFO"
```

### Production Configuration

For production environments, update allowed origins:

```bash
CORS__ALLOWED_ORIGINS='["https://yourdomain.com", "https://www.yourdomain.com"]'
LOGGING__LEVEL="WARNING"
```

## Request Logging

### Features

1. **Correlation ID Tracking**
   - Each request gets a unique UUID
   - Available in `request.state.correlation_id`
   - Returned in `X-Correlation-ID` response header
   - Logged with all request-related messages

2. **Performance Monitoring**
   - Tracks request processing time
   - Returned in `X-Process-Time` response header
   - Logged in seconds with 3 decimal precision

3. **Structured Logging**
   - Consistent log format across the application
   - Extra fields for filtering and analysis
   - Automatic error logging with stack traces

4. **Smart Path Filtering**
   - Excludes health checks and documentation endpoints
   - Reduces log noise in production
   - Configurable via `EXCLUDED_PATHS`

### Log Output Format

```
2025-10-30 03:14:18 - app.core.middleware - INFO - Request started
2025-10-30 03:14:18 - app.core.middleware - INFO - Request completed
```

With structured extra data:
```json
{
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/api/v1/listings",
  "client_host": "127.0.0.1",
  "user_agent": "Mozilla/5.0...",
  "status_code": 200,
  "process_time": "0.123s"
}
```

### Error Logging

Failed requests are logged with ERROR level and include:
- Exception type and message
- Full stack trace
- Request details for debugging
- Processing time up to failure point

### Custom Headers

All responses include:
- `X-Correlation-ID`: Unique request identifier
- `X-Process-Time`: Processing duration in seconds

## CORS Configuration

### Default Settings

The middleware is pre-configured for local development:

- **Allowed Origins**: `http://localhost:3000`, `http://localhost:5173`
- **Allow Credentials**: `true` (enables cookies/authentication)
- **Allowed Methods**: All standard HTTP methods
- **Allowed Headers**: `*` (all headers)

### How CORS Works

1. Browser sends preflight OPTIONS request
2. Server responds with allowed origins/methods/headers
3. Browser validates response
4. If valid, actual request is sent

### Customizing CORS

#### Add Additional Origins

```bash
CORS__ALLOWED_ORIGINS='["http://localhost:3000", "https://staging.example.com", "https://example.com"]'
```

#### Restrict HTTP Methods

```bash
CORS__ALLOWED_METHODS='["GET", "POST", "PUT", "DELETE"]'
```

#### Restrict Headers

```bash
CORS__ALLOWED_HEADERS='["Content-Type", "Authorization", "X-Custom-Header"]'
```

## Middleware Order

Middleware is applied in reverse order of registration. Current order:

```python
# 1. CORS (applied first - validates origin)
app.add_middleware(CORSMiddleware, ...)

# 2. Request Logging (applied second - logs valid requests)
app.add_middleware(RequestLoggingMiddleware)

# 3. Application routes (applied last)
app.include_router(api_router)
```

**Important**: CORS middleware must be registered before other middleware to properly handle preflight requests.

## Usage Examples

### Accessing Correlation ID in Routes

```python
from fastapi import Request

@router.get("/example")
async def example_route(request: Request):
    correlation_id = request.state.correlation_id
    # Use for logging, error tracking, etc.
    return {"correlation_id": correlation_id}
```

### Custom Logging in Services

```python
import logging

logger = logging.getLogger(__name__)

def process_listing(listing_id: str):
    logger.info(
        "Processing listing",
        extra={"listing_id": listing_id}
    )
```

### Testing CORS

```bash
# Test preflight request
curl -X OPTIONS http://localhost:8000/api/v1/listings \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Expected response headers:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
# Access-Control-Allow-Headers: *
```

## Best Practices

### Logging

1. **Use Appropriate Log Levels**
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages (4xx responses)
   - ERROR: Error messages (5xx responses, exceptions)
   - CRITICAL: Critical errors requiring immediate attention

2. **Include Context**
   - Always log relevant identifiers (user_id, listing_id, etc.)
   - Use structured logging with extra fields
   - Include correlation_id for request tracking

3. **Avoid Sensitive Data**
   - Never log passwords, tokens, or personal data
   - Mask sensitive fields in structured logs

### CORS

1. **Production Security**
   - Specify exact allowed origins (never use `*` in production)
   - Limit allowed methods to those actually used
   - Review allowed headers regularly

2. **Credentials**
   - Only enable credentials if needed for authentication
   - Ensure HTTPS in production when using credentials

3. **Testing**
   - Test CORS from actual frontend during development
   - Verify preflight requests work correctly
   - Check browser console for CORS errors

## Troubleshooting

### CORS Errors

**Problem**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solutions**:
1. Verify origin is in `CORS__ALLOWED_ORIGINS`
2. Check middleware order (CORS must be first)
3. Ensure frontend URL matches exactly (include port)

### Logging Issues

**Problem**: Not seeing expected logs

**Solutions**:
1. Check `LOGGING__LEVEL` setting
2. Verify logger name matches module
3. Check if path is in `EXCLUDED_PATHS`

**Problem**: Too many logs

**Solutions**:
1. Increase log level to WARNING or ERROR
2. Add paths to `EXCLUDED_PATHS`
3. Use log filtering in production

## Performance Considerations

1. **Minimal Overhead**
   - Middleware adds ~1-5ms per request
   - UUID generation is fast
   - Logging is asynchronous

2. **Excluded Paths**
   - Health checks and docs are excluded by default
   - Reduces unnecessary logging
   - Improves performance for high-frequency endpoints

3. **Production Optimization**
   - Use WARNING level in production
   - Configure log aggregation (e.g., CloudWatch, ELK)
   - Monitor correlation IDs for request tracing

## Future Enhancements

Potential improvements:

1. **Rate Limiting Middleware**
   - Prevent abuse
   - Configurable limits per endpoint

2. **Request ID Propagation**
   - Pass correlation_id to external services
   - End-to-end request tracing

3. **Metrics Collection**
   - Prometheus-compatible metrics
   - Response time histograms
   - Error rate tracking

4. **Advanced Logging**
   - JSON logging for structured parsing
   - Log rotation and archival
   - Integration with external logging services

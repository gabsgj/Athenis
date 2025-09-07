import os
from functools import wraps
from flask import request as flask_request, jsonify


class AuthError(Exception):
    """Custom exception for authentication errors with HTTP context."""
    def __init__(self, message: str = "Unauthorized", status_code: int = 401, error_code: str = "E401_UNAUTHORIZED"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


def require_api_key(func_or_key=None):
    """
    Flexible API-key check decorator.
    Can be used as @require_api_key or @require_api_key("custom_key")
    """
    
    def _check(req, expected_key=None):
        hdr = None
        try:
            hdr = req.headers.get("X-API-Key")
        except Exception:
            # fallback to global request
            hdr = flask_request.headers.get("X-API-Key")
        exp = expected_key or os.getenv("API_KEY", "secret123")
        if not hdr:
            raise AuthError("Missing API key", status_code=401, error_code="E401_MISSING_API_KEY")
        if hdr != exp:
            raise AuthError("Invalid API key", status_code=401, error_code="E401_INVALID_API_KEY")

    def decorator(func, expected_key=None):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _check(flask_request, expected_key)
            return func(*args, **kwargs)
        return wrapper

    # If called with a function (no parentheses), return the decorated function
    if callable(func_or_key):
        return decorator(func_or_key)
    
    # If called with arguments or no arguments, return a decorator function
    expected_key = func_or_key if isinstance(func_or_key, str) else None
    return lambda func: decorator(func, expected_key)


def error_response(code: str, message: str, status: int = 400):
    """Return a standardized JSON error response matching app expectations."""
    return jsonify({
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        }
    }), status

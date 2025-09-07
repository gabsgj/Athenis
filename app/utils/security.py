import os
from flask import request as flask_request, jsonify


class AuthError(Exception):
    """Custom exception for authentication errors with HTTP context."""
    def __init__(self, message: str = "Unauthorized", status_code: int = 401, error_code: str = "E401_UNAUTHORIZED"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


def require_api_key(arg=None):
    """
    Flexible API-key check:
    - If passed a Flask request-like object, perform the check immediately.
    - If called with no args or a string, behave as a decorator with expected key.
    """
    expected_key = arg if isinstance(arg, str) or arg is None else None

    def _check(req):
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

    # Direct-check mode
    if hasattr(arg, "headers"):
        _check(arg)
        return True

    # Decorator mode
    def decorator(func):
        def wrapper(*args, **kwargs):
            _check(flask_request)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def error_response(code: str, message: str, status: int = 400):
    """Return a standardized JSON error response matching app expectations."""
    return jsonify({
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        }
    }), status

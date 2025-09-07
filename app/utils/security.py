from flask import request, jsonify

class AuthError(Exception):
    """Custom exception for authentication errors."""
    pass

def require_api_key(expected_key="secret123"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            api_key = request.headers.get("X-API-Key")
            if not api_key:
                raise AuthError("Missing API key")
            if api_key != expected_key:
                raise AuthError("Invalid API key")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def error_response(message, code=400):
    """Return a standardized JSON error response."""
    return jsonify({
        "success": False,
        "error": {
            "message": message,
            "code": code
        }
    }), code

from functools import wraps
from flask import request, jsonify

API_KEY = "secret123"  # replace with env var in production

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            return jsonify({"error": "Invalid or missing API key", "code": "ERR_INVALID_API_KEY"}), 401
        return func(*args, **kwargs)
    return wrapper

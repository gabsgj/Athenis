import os
from functools import wraps
from flask import request, jsonify


def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = os.getenv("API_KEY")
        provided = request.headers.get("x-api-key") or request.args.get("api_key")
        if not api_key or provided != api_key:
            return jsonify({"error": "unauthorized", "message": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return wrapper


def set_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:"
    return resp

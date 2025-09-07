# utils/security.py
import os
from flask import Request, jsonify

class AuthError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message

def require_api_key(request: Request) -> None:
    """
    Enforce API key on ALL /api/* endpoints.
    Reads env var API_KEY and matches against 'X-API-Key' header.
    """
    expected = (os.getenv("API_KEY") or "").strip()
    if not expected:
        raise AuthError(status_code=401, error_code="E401_API_KEY_NOT_SET",
                        message="Server misconfiguration: API_KEY is not set.")
    provided = (request.headers.get("X-API-Key") or "").strip()
    if not provided:
        raise AuthError(status_code=401, error_code="E401_MISSING_API_KEY",
                        message="Missing X-API-Key header.")
    if provided != expected:
        raise AuthError(status_code=401, error_code="E401_INVALID_API_KEY",
                        message="Invalid API key.")

def error_response(code: str, message: str, status: int = 400):
    return jsonify({"ok": False, "error": {"code": code, "message": message}}), status

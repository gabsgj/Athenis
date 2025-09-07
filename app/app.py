import os

if os.getenv("FAST_TEST") == "1":
    # Stub the ModelManager
    from app.models.model_manager import ModelManager as RealModelManager

    class ModelManagerStub(RealModelManager):
        def analyze_document(self, text, mode, stream=False, target_lang="hi"):
            stub_text = f"[{mode.upper()} stub] {text[:50]}"
            if stream:
                for word in stub_text.split():
                    yield word + " "
            else:
                return stub_text

    model = ModelManagerStub()

    # Stub the risk analyzer
    def analyze_risk(text):
        return [
            {
                "id": 1,
                "type": "stub",
                "clause_excerpt": text[:50],
                "severity": "low",
                "explanation": "This is a stubbed risk for testing",
                "suggested_action": "none"
            }
        ]

import json
from typing import Generator, Any, Dict

from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
import requests as httpx
from flask_cors import CORS

from app.models.model_manager import ModelManager, ModelError
from app.utils.security import require_api_key, AuthError, error_response
from app.utils.sse import sse_event, sse_from_text_stream
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.metrics import Metrics


# Risk analyzer (teammate 2)
try:
    from app.services.risk_analyzer import analyze_risk  # type: ignore
except Exception:
    analyze_risk = None  # handled gracefully

app = Flask(__name__)
# Broad CORS for frontend teammate; restrict in prod as needed
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

model = ModelManager()
metrics = Metrics()

# Internal service base (used for proxying file uploads):
GOFR_URL = os.getenv("GOFR_URL", "http://localhost:8090").rstrip("/")

# ---------------------------
# Helper functions
# ---------------------------

def _wants_streaming(req) -> bool:
    """Check if client requested streaming"""
    qs = req.args.get("stream")
    if qs is not None:
        return qs.lower() in {"1", "true", "yes"}
    try:
        body = req.get_json(silent=True) or {}
        if isinstance(body, dict):
            if str(body.get("stream", "")).lower() in {"1", "true", "yes"}:
                return True
    except Exception:
        pass
    accept = (req.headers.get("Accept") or "").lower()
    return "text/event-stream" in accept

def _get_text() -> str:
    if not request.is_json:
        raise AuthError(
            status_code=415,
            error_code="E415_UNSUPPORTED_MEDIA_TYPE",
            message="Content-Type must be application/json",
        )
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        raise AuthError(
            status_code=400,
            error_code="E400_MISSING_TEXT",
            message="Field 'text' is required and must be non-empty.",
        )
    return text

def _translate_target_lang(data: Dict[str, Any]) -> str:
    tgt = (data.get("target_lang") or "").strip().lower()
    if tgt in {"en", "hi"}:
        return tgt
    text = (data.get("text") or "")
    from app.models.model_manager import _looks_hindi
    return "en" if _looks_hindi(text) else "hi"

def _stream_response(gen: Generator[str, None, None], event: str = "chunk") -> Response:
    return Response(
        stream_with_context(sse_from_text_stream(gen, event=event)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )

# ---------------------------
# Error handlers
# ---------------------------

@app.errorhandler(AuthError)
def _auth_error_handler(err: AuthError):
    return jsonify({
        "ok": False,
        "error": {"code": err.error_code, "message": err.message}
    }), err.status_code

@app.errorhandler(404)
def _not_found(_):
    return jsonify({"ok": False, "error": {"code": "E404_NOT_FOUND", "message": "Not found"}}), 404

@app.errorhandler(Exception)
def _unhandled(e: Exception):
    return jsonify({"ok": False, "error": {"code": "E500_INTERNAL", "message": "Internal server error"}}), 500

# ---------------------------
# Health endpoints
# ---------------------------

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "backend", "streaming": True})

@app.get("/api/v1/health")
def health_v1():
    return jsonify({"ok": True, "service": "backend", "streaming": True})

@app.get("/metrics")
def metrics_endpoint():
    data = generate_latest(metrics.registry)
    return Response(data, mimetype=CONTENT_TYPE_LATEST)

# ---------------------------
# Frontend: serve UI
# ---------------------------

@app.get("/")
def index():
    return send_from_directory(os.path.join(app.root_path, "templates"), "index.html")

@app.get("/main.js")
def serve_main_js():
    return send_from_directory(os.path.join(app.root_path, "templates"), "main.js")

@app.get("/styles.css")
def serve_styles_css():
    return send_from_directory(os.path.join(app.root_path, "templates"), "styles.css")

@app.get("/public/<path:filename>")
def serve_public(filename: str):
    return send_from_directory(os.path.join(app.root_path, "templates", "public"), filename)

# ---------------------------
# Proxy: /gofr -> Go ingestion service
# ---------------------------

@app.post("/gofr/ingest")
def proxy_gofr_ingest():
    try:
        files = {}
        if "file" in request.files:
            f = request.files["file"]
            files["file"] = (f.filename, f.stream, f.mimetype)
        data = dict(request.form)
        url = f"{GOFR_URL}/ingest"
        resp = httpx.post(url, files=files or None, data=data, timeout=60)
        return Response(resp.content, status=resp.status_code, headers={"Content-Type": resp.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"error": "proxy_failed", "detail": str(e)}), 502

# ---------------------------
# v1 Inference (generic task)
# ---------------------------

@app.post("/api/v1/inference")
def inference_v1():
    require_api_key(request)
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    task = (data.get("task") or "").strip()
    
    if not text:
        raise AuthError(status_code=400, error_code="E400_MISSING_TEXT",
                        message="Field 'text' is required and must be non-empty.")
    
    try:
        if task == "simplify":
            result = model.analyze_document(text=text, mode="simplify", stream=False)
        elif task == "summarize":
            result = model.analyze_document(text=text, mode="summarize", stream=False)
        elif task == "translate":
            target_lang = _translate_target_lang(data)
            result = model.analyze_document(text=text, mode="translate", stream=False, target_lang=target_lang)
        else:
            result = model.analyze_document(text=text, mode="simplify", stream=False)
            
        return jsonify({"ok": True, "task": task, "result": result})
    except ModelError as e:
        return error_response("E502_LLM_FAILURE", f"{e}", status=502)

# ---------------------------
# Core endpoints
# ---------------------------

@app.post("/api/simplify")
def simplify():
    require_api_key(request)
    text = _get_text()
    stream = _wants_streaming(request)
    try:
        if stream:
            gen = model.analyze_document(text=text, mode="simplify", stream=True)
            return _stream_response(gen, event="simplify")
        out = model.analyze_document(text=text, mode="simplify", stream=False)
        return jsonify({"ok": True, "mode": "simplify", "result": out})
    except ModelError as e:
        return error_response("E502_LLM_FAILURE", f"{e}", status=502)

@app.post("/api/summarize")
def summarize():
    require_api_key(request)
    text = _get_text()
    stream = _wants_streaming(request)
    try:
        if stream:
            gen = model.analyze_document(text=text, mode="summarize", stream=True)
            return _stream_response(gen, event="summarize")
        out = model.analyze_document(text=text, mode="summarize", stream=False)
        return jsonify({"ok": True, "mode": "summarize", "result": out})
    except ModelError as e:
        return error_response("E502_LLM_FAILURE", f"{e}", status=502)

@app.post("/api/translate")
def translate():
    require_api_key(request)
    if not request.is_json:
        raise AuthError(status_code=415, error_code="E415_UNSUPPORTED_MEDIA_TYPE",
                        message="Content-Type must be application/json")
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        raise AuthError(status_code=400, error_code="E400_MISSING_TEXT",
                        message="Field 'text' is required and must be non-empty.")
    target_lang = _translate_target_lang(data)
    stream = _wants_streaming(request)

    try:
        if stream:
            gen = model.analyze_document(text=text, mode="translate", stream=True, target_lang=target_lang)
            return _stream_response(gen, event="translate")
        out = model.analyze_document(text=text, mode="translate", stream=False, target_lang=target_lang)
        return jsonify({"ok": True, "mode": "translate", "target_lang": target_lang, "result": out})
    except ModelError as e:
        return error_response("E502_LLM_FAILURE", f"{e}", status=502)

# app/app.py

# ... (all imports and other functions) ...

@app.post("/api/full-analysis")
def full_analysis():
    """
    Returns JSON with:
      - simplified
      - summary
      - risk (from teammate 2 or stub if FAST_TEST)
    Supports SSE streaming
    """
    require_api_key(request)
    text = _get_text()
    stream = _wants_streaming(request)

    # Use stub risk analyzer in FAST_TEST mode
    if os.getenv("FAST_TEST") == "1" or analyze_risk is None:
        def analyze_risk_stub(txt):
            return [
                {
                    "id": "risk_stub",
                    "type": "test",
                    "clause_excerpt": txt[:50],
                    "severity": "low",
                    "explanation": "stub explanation",
                    "suggested_action": "none",
                }
            ]
        current_risk_analyzer = analyze_risk_stub
    else:
        current_risk_analyzer = analyze_risk

    def gen_stream():
        # Simplify
        try:
            for chunk in model.analyze_document(text=text, mode="simplify", stream=True):
                yield sse_event(chunk, event="simplify")
        except ModelError as e:
            yield sse_event({"code": "E502_LLM_FAILURE", "message": str(e)}, event="error")
            yield sse_event("", event="done")
            return

        # Summarize
        try:
            for chunk in model.analyze_document(text=text, mode="summarize", stream=True):
                yield sse_event(chunk, event="summarize")
        except ModelError as e:
            yield sse_event({"code": "E502_LLM_FAILURE", "message": str(e)}, event="error")
            yield sse_event("", event="done")
            return

        # Risk (send once)
        try:
            risk = current_risk_analyzer(text)
            yield sse_event(risk, event="risk")
        except Exception as e:
            yield sse_event({"code": "E503_RISK_ANALYZER_UNAVAILABLE", "message": f"{e}"}, event="error")

        yield sse_event("", event="done")

    if stream:
        return Response(
            stream_with_context(gen_stream()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            },
        )

    # Synchronous JSON path
    try:
        simplified = model.analyze_document(text=text, mode="simplify", stream=False)
        summary = model.analyze_document(text=text, mode="summarize", stream=False)
    except ModelError as e:
        return error_response("E502_LLM_FAILURE", f"{e}", status=502)

    try:
        risk = current_risk_analyzer(text)
    except Exception as e:
        return error_response("E503_RISK_ANALYZER_UNAVAILABLE", f"{e}", status=503)

    return jsonify({
        "ok": True,
        "mode": "full-analysis",
        "result": {
            "simplified": simplified,
            "summary": summary,
            "risk": risk
        }
    })


# ---------------------------
# Factory
# ---------------------------

def create_app():
    """Create and configure the Flask app for testing"""
    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(debug=True, host="0.0.0.0", port=port)

# ---------------------------
# Factory
# ---------------------------

def create_app():
    """Create and configure the Flask app for testing"""
    return app

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
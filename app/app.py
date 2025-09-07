import os
from functools import wraps
from werkzeug.utils import secure_filename
import tempfile

# Optional torch import for GPU support
try:
    import torch
except ImportError:
    class TorchStub:
        class cuda:
            @staticmethod
            def is_available():
                return False
            @staticmethod
            def memory_allocated():
                return 0
    torch = TorchStub()

from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
from flask_cors import CORS
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Local imports
from app.utils.security import require_api_key, AuthError
from app.utils.sse import sse_from_text_stream
from app.utils.cache import Cache
from app.utils.extract import extract_pdf, extract_docx, extract_txt, maybe_truncate
from app.utils.rate_limiter import RateLimiter
from app.utils.metrics import Metrics
from app.models.model_manager import ModelManager, ModelError
from app.models.risk_detector import full_clause_analysis

def create_app():
    """Creates and configures the Flask app."""
    app = Flask(__name__, static_folder='templates', static_url_path='')

    # --- Configuration ---
    is_fast_test = os.getenv("FAST_TEST") == "1"
    app.config["IS_FAST_TEST"] = is_fast_test
    app.config["MODEL_NAME"] = os.getenv("MODEL_NAME", "default-model")

    # --- CORS ---
    cors_origins = os.getenv("CORS_ORIGINS")
    if cors_origins:
        CORS(app, resources={r"/api/*": {"origins": cors_origins.split(',')}})

    # --- Services ---
    app.model_manager = ModelManager()
    app.rate_limiter = RateLimiter(rate_per_minute=int(os.getenv("RATE_LIMIT_PER_MIN", 60)))
    app.cache = Cache()
    app.metrics = Metrics()

    # --- Helpers ---
    def ok(data, status_code=200):
        return jsonify({"ok": True, **data}), status_code

    def error_response(code, message, status_code):
        return jsonify({"ok": False, "error": {"code": code, "message": message}}), status_code

    # --- Decorators ---
    def apply_rate_limit(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.headers.get("X-API-Key", request.remote_addr)
            if not app.rate_limiter.allow(key):
                return error_response("E429_RATE_LIMIT_EXCEEDED", "Rate limit exceeded", 429)
            return f(*args, **kwargs)
        return decorated_function

    # --- Error Handlers ---
    @app.errorhandler(AuthError)
    def handle_auth_error(err):
        return error_response(err.error_code, err.message, err.status_code)

    @app.errorhandler(404)
    def not_found(err):
        return error_response("E404_NOT_FOUND", "The requested resource was not found.", 404)
    
    @app.errorhandler(405)
    def method_not_allowed(err):
        return error_response("E405_METHOD_NOT_ALLOWED", "The method is not allowed for the requested URL.", 405)

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        app.logger.error(f"Unhandled exception: {e}", exc_info=True)
        return error_response("E500_INTERNAL_SERVER_ERROR", "An unexpected internal error occurred.", 500)

    # --- Routes ---
    @app.route("/")
    def index():
        return send_from_directory("templates", "index.html")

    @app.route("/main.js")
    def main_js():
        return send_from_directory("templates", "main.js")

    @app.route("/styles.css")
    def styles_css():
        return send_from_directory("templates", "styles.css")

    @app.route("/api/v1/health")
    def health_check():
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return ok({
            "status": "ready",
            "model": app.model_manager.model_name,
            "device": device
        })

    @app.route("/metrics")
    @require_api_key
    def metrics():
        if torch.cuda.is_available():
            app.metrics.gpu_memory_used.set(torch.cuda.memory_allocated())
        app.metrics.requests_total.inc()
        return Response(generate_latest(app.metrics.registry), mimetype=CONTENT_TYPE_LATEST)

    def process_request(task, text, stream=False, target_lang=None):
        if not text:
            return error_response("E400_BAD_REQUEST", "Missing 'text' field.", 400)
        
        try:
            if stream:
                def generate():
                    for chunk in app.model_manager.stream_process(text, task, language=target_lang):
                        yield f"event: chunk\ndata: {chunk}\n\n"
                    yield "event: done\ndata: {}\n\n"
                return Response(stream_with_context(generate()), mimetype="text/event-stream")
            else:
                result = app.model_manager.process(text, task, language=target_lang)
                return ok({"result": result})
        except ModelError as e:
            return error_response("E500_MODEL_ERROR", str(e), 500)

    @app.route("/gofr/ingest", methods=["POST", "OPTIONS"])
    @apply_rate_limit
    def ingest():
        # CORS preflight
        if request.method == "OPTIONS":
            resp = jsonify({})
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
            return resp, 204

        # OPTIONAL auth (same as other API). If you want uploads protected, uncomment next line:
        # require_api_key(lambda: None)();  # or decorate the function with @require_api_key

        if "file" not in request.files:
            return error_response("E400_NO_FILE", "No file provided", 400)
        f = request.files["file"]
        if not f.filename:
            return error_response("E400_EMPTY_NAME", "Empty filename", 400)

        filename = secure_filename(f.filename)
        with tempfile.TemporaryDirectory() as tdir:
            path = os.path.join(tdir, filename)
            f.save(path)
            ext = os.path.splitext(filename)[1].lower()

            try:
                if ext == ".pdf":
                    text = extract_pdf(path)
                elif ext == ".docx":
                    text = extract_docx(path)
                else:
                    text = extract_txt(path)
            except Exception as e:
                return error_response("E422_EXTRACT_FAIL", f"Extraction failed: {e}", 422)

        # Keep output reasonable
        text = maybe_truncate(text, int(os.getenv("MAX_EXTRACT_BYTES", str(5 * 1024 * 1024))))
        return ok({"text": text})

    @app.route("/api/simplify", methods=["POST"])
    @require_api_key
    @apply_rate_limit
    def simplify():
        return process_request("simplify", request.json.get("text"))

    @app.route("/api/summarize", methods=["POST"])
    @require_api_key
    @apply_rate_limit
    def summarize():
        return process_request("summarize", request.json.get("text"))

    @app.route("/api/translate", methods=["POST"])
    @require_api_key
    @apply_rate_limit
    def translate():
        data = request.get_json()
        return process_request("translate", data.get("text"), target_lang=data.get("target_lang", "en"))

    @app.route("/api/full-analysis", methods=["POST"])
    @require_api_key
    @apply_rate_limit
    def full_analysis():
        text = request.json.get("text")
        if not text:
            return error_response("E400_BAD_REQUEST", "Missing 'text' field.", 400)
        try:
            simplified = app.model_manager.process(text, "simplify")
            summary = app.model_manager.process(text, "summarize")
            risks = full_clause_analysis(text)
            return ok({"result": {"simplified": simplified, "summary": summary, "risk": risks}})
        except ModelError as e:
            return error_response("E500_MODEL_ERROR", str(e), 500)

    @app.route("/api/v1/inference", methods=["POST"])
    @require_api_key
    @apply_rate_limit
    def inference():
        data = request.get_json()
        return process_request(
            task=data.get("task", "simplify"),
            text=data.get("text"),
            stream=data.get("stream", False),
            target_lang=data.get("target_lang")
        )

    return app

# --- Main Execution ---
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
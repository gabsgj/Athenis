import os
import json
import time
from functools import wraps
from queue import Queue
from threading import Thread
from typing import Dict, Any, Generator

from flask import Flask, jsonify, request, Response, send_from_directory, render_template
from flask_cors import CORS
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from app.models.model_manager import ModelManager
from app.utils.cache import Cache
from app.utils.rate_limiter import RateLimiter
from app.utils.security import require_api_key, set_security_headers
from app.utils.sse import sse_format
from app.utils.metrics import Metrics
from app.utils.logging import logger


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)

    # Security headers after each request
    app.after_request(set_security_headers)

    # Metrics
    metrics = Metrics()

    # Cache (LRU or Redis)
    cache = Cache(os.getenv("REDIS_URL"))

    # Model manager
    model = ModelManager(cache=cache)

    # Rate limiter
    rate = RateLimiter(int(os.getenv("RATE_LIMIT_PER_MIN", "60")))

    def rate_limited(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            identifier = request.headers.get("x-api-key") or request.remote_addr
            if not rate.allow(identifier):
                return jsonify({
                    "error": "rate_limited",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": 60
                }), 429
            return f(*args, **kwargs)
        return wrapper

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/v1/health")
    def health():
        gpu = model.gpu_info()
        try:
            metrics.gpu_memory_used.set(gpu.get("memory", 0))
            metrics.requests_total.labels(endpoint="health", method="GET", status="200").inc()
        except Exception:
            pass
        return jsonify({"status": "ok", "gpu": gpu, "model": model.model_name})

    @app.route("/metrics")
    def metrics_endpoint():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.route("/api/v1/upload", methods=["POST"])
    @require_api_key
    @rate_limited
    def upload():
        # Forward to Go service or handle text directly
        file = request.files.get("file")
        text = request.form.get("text")
        go_url = os.getenv("GOFR_URL", "http://gofr:8090")
        import requests as pyrequests
        if file:
            files = {"file": (file.filename, file.stream, file.mimetype)}
            resp = pyrequests.post(f"{go_url}/ingest", files=files, timeout=120)
            data = resp.json()
            import uuid
            data.update({"upload_id": str(uuid.uuid4())})
            return jsonify(data), resp.status_code
        elif text:
            resp = pyrequests.post(f"{go_url}/ingest", data={"text": text}, timeout=120)
            data = resp.json()
            import uuid
            data.update({"upload_id": str(uuid.uuid4())})
            return jsonify(data), resp.status_code
        else:
            return jsonify({"error": "no_input", "message": "Provide file or text"}), 400

    @app.route("/api/v1/inference", methods=["POST"])
    @require_api_key
    @rate_limited
    def inference():
        payload = request.get_json(force=True)
        text = payload.get("text", "")
        task = payload.get("task", "simplify")
        language = payload.get("language", "auto")
        start = time.time()
        try:
            result = model.process(text=text, task=task, language=language)
            metrics.request_latency.observe(time.time() - start)
            metrics.requests_total.labels(endpoint="inference", method="POST", status="200").inc()
            return jsonify(result)
        except Exception as e:
            logger.exception("inference_error")
            metrics.requests_total.labels(endpoint="inference", method="POST", status="500").inc()
            return jsonify({"error": "inference_error", "message": str(e)}), 500

    @app.route("/api/v1/stream", methods=["POST"])
    @require_api_key
    @rate_limited
    def stream():
        payload = request.get_json(force=True)
        text = payload.get("text", "")
        task = payload.get("task", "simplify")
        language = payload.get("language", "auto")

        def generate() -> Generator[str, None, None]:
            try:
                yield sse_format("progress", {"stage": "start"})
                for event in model.stream_process(text=text, task=task, language=language):
                    yield sse_format("token", event)
                yield sse_format("progress", {"stage": "finish"})
                yield sse_format("done", "true")
            except Exception as e:
                yield sse_format("error", str(e))
        return Response(generate(), mimetype="text/event-stream")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from app.models.model_manager import ModelManager
from app.utils.security import require_api_key
from app.utils import sse

# Import teammate 2's risk analyzer
try:
    from app.risk_module import risk_analyzer
except ImportError:
    risk_analyzer = None

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend
model = ModelManager()

# Utility: error response
def error_response(message, code):
    return jsonify({"error": message, "code": code}), 400

@app.route("/api/simplify", methods=["POST"])
@require_api_key
def simplify():
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text:
        return error_response("Missing input text", "ERR_MISSING_TEXT")

    stream = request.args.get("stream") == "true"
    if stream:
        return Response(sse.stream(model.analyze_document(text, "simplify", stream=True)),
                        mimetype="text/event-stream")
    return jsonify({"result": model.analyze_document(text, "simplify")})

@app.route("/api/summarize", methods=["POST"])
@require_api_key
def summarize():
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text:
        return error_response("Missing input text", "ERR_MISSING_TEXT")

    stream = request.args.get("stream") == "true"
    if stream:
        return Response(sse.stream(model.analyze_document(text, "summarize", stream=True)),
                        mimetype="text/event-stream")
    return jsonify({"result": model.analyze_document(text, "summarize")})

@app.route("/api/translate", methods=["POST"])
@require_api_key
def translate():
    data = request.get_json(force=True)
    text = data.get("text", "")
    target = data.get("target_lang", "hi")
    if not text:
        return error_response("Missing input text", "ERR_MISSING_TEXT")

    stream = request.args.get("stream") == "true"
    if stream:
        return Response(sse.stream(model.analyze_document(text, "translate", stream=True, target_lang=target)),
                        mimetype="text/event-stream")
    return jsonify({"result": model.analyze_document(text, "translate", target_lang=target)})

@app.route("/api/full-analysis", methods=["POST"])
@require_api_key
def full_analysis():
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text:
        return error_response("Missing input text", "ERR_MISSING_TEXT")

    simplified = model.analyze_document(text, "simplify")
    summary = model.analyze_document(text, "summarize")
    risk = None
    if risk_analyzer:
        risk = risk_analyzer(text)

    return jsonify({
        "simplified": simplified,
        "summary": summary,
        "risk_analysis": risk
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)

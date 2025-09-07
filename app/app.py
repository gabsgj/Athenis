# app/app.py

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from app.models.model_manager import ModelManager
from app.utils import security

# Mock LLM client
class DummyLLMClient:
    def complete(self, prompt: str) -> str:
        return f"[LLM output] {prompt[:60]}..."

    def stream(self, prompt: str):
        for word in prompt.split():
            yield word + " "

llm_client = DummyLLMClient()
model_manager = ModelManager(llm_client)

app = Flask(__name__)
CORS(app)  # enable CORS for frontend teammate

def require_api_key():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return {"error": True, "code": 1001, "message": "Missing API key"}, 401
    if not security.verify_api_key(api_key):
        return {"error": True, "code": 1002, "message": "Invalid API key"}, 403
    return None

@app.route("/api/simplify", methods=["POST"])
def simplify():
    check = require_api_key()
    if check: return jsonify(check[0]), check[1]

    data = request.json or {}
    text = data.get("text")
    stream = data.get("stream", False)

    result = model_manager.analyze_document(text, mode="simplify", stream=stream)
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    if stream:
        return Response(result, mimetype="text/event-stream")
    return jsonify(result)

@app.route("/api/summarize", methods=["POST"])
def summarize():
    check = require_api_key()
    if check: return jsonify(check[0]), check[1]

    data = request.json or {}
    text = data.get("text")
    stream = data.get("stream", False)

    result = model_manager.analyze_document(text, mode="summarize", stream=stream)
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    if stream:
        return Response(result, mimetype="text/event-stream")
    return jsonify(result)

@app.route("/api/translate", methods=["POST"])
def translate():
    check = require_api_key()
    if check: return jsonify(check[0]), check[1]

    data = request.json or {}
    text = data.get("text")
    target_lang = data.get("target_lang")
    stream = data.get("stream", False)

    result = model_manager.analyze_document(
        text, mode="translate", stream=stream, target_lang=target_lang
    )
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    if stream:
        return Response(result, mimetype="text/event-stream")
    return jsonify(result)

@app.route("/api/full-analysis", methods=["POST"])
def full_analysis():
    check = require_api_key()
    if check: return jsonify(check[0]), check[1]

    data = request.json or {}
    text = data.get("text")
    if not text:
        return jsonify({"error": True, "code": 2001, "message": "Text not provided"}), 400

    try:
        simplified = model_manager.analyze_document(text, mode="simplify")
        summarized = model_manager.analyze_document(text, mode="summarize")
        
        # Risk detection from teammate 2 (do not modify)
        from app.teammate2.risk_module import analyze_risk
        risk = analyze_risk(text)

        return jsonify({
            "simplified": simplified.get("result"),
            "summary": summarized.get("result"),
            "risk": risk
        })

    except Exception as e:
        return jsonify({
            "error": True,
            "code": 3002,
            "message": f"Full-analysis processing error: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(debug=True)

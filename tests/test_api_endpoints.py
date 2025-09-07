import json
import os
import pytest
from app.app import create_app

@pytest.fixture
def app():
    # Set external API mode to avoid model loading issues in tests
    os.environ["EXTERNAL_LLM_API_URL"] = "http://dummy-test-api.com"
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_simplify(client):
    res = client.post("/api/simplify", 
                      json={"text": "This is a complicated demonstration."}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    assert "result" in res.get_json()

def test_summarize(client):
    res = client.post("/api/summarize", 
                      json={"text": "First sentence. Second sentence. Third sentence."}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    assert "result" in res.get_json()

def test_translate(client):
    res = client.post("/api/translate", 
                      json={"text": "hello world", "target_lang": "hi"}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    assert "result" in res.get_json()

def test_full_analysis(client):
    res = client.post("/api/full-analysis",
                      json={"text": "This is a risk analysis test."},
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    data = res.get_json()
    # check inside the 'result' key
    assert "simplified" in data["result"]
    assert "summary" in data["result"]
    assert "risk" in data["result"]

def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ready"



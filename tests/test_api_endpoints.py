import json
from app.app import app

client = app.test_client()

def test_simplify():
    res = client.post("/api/simplify", 
                      json={"text": "This is a complicated demonstration."}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    assert "result" in res.get_json()

def test_summarize():
    res = client.post("/api/summarize", 
                      json={"text": "First sentence. Second sentence. Third sentence."}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    assert "result" in res.get_json()

def test_translate():
    res = client.post("/api/translate", 
                      json={"text": "hello world", "target_lang": "hi"}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    assert "result" in res.get_json()

def test_full_analysis():
    res = client.post("/api/full-analysis", 
                      json={"text": "This is a risk analysis test."}, 
                      headers={"X-API-Key": "secret123"})
    assert res.status_code == 200
    data = res.get_json()
    assert "simplified" in data
    assert "summary" in data
    assert "risk_analysis" in data

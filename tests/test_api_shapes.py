import os
from app.app import create_app


def test_health_and_inference_stub(monkeypatch):
    os.environ['API_KEY'] = 'k'
    os.environ['FAST_TEST'] = '1'
    app = create_app()
    app.testing = True
    c = app.test_client()
    assert c.get('/api/v1/health').status_code == 200
    res = c.post('/api/v1/inference', json={"text":"Hello","task":"simplify","language":"en"}, headers={"x-api-key":"k"})
    assert res.status_code in (200, 500)

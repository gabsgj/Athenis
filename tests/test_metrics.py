from app.app import app


def test_metrics_endpoint_ok():
    client = app.test_client()
    res = client.get('/metrics')
    assert res.status_code == 200
    # Prometheus text format content type
    assert 'text/plain' in (res.headers.get('Content-Type') or '')
    body = res.get_data(as_text=True)
    assert isinstance(body, str)
    # Should at least include a HELP/TYPE line for one of our metrics
    assert 'requests_total' in body or 'request_latency_seconds' in body or 'gpu_memory_used_bytes' in body

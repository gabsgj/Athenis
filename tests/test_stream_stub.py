from app.models.model_manager import ModelManager
from app.utils.cache import Cache
import os

def test_stream_tokens_stub(monkeypatch):
    os.environ['FAST_TEST'] = '1'
    mm = ModelManager()
    tokens = list(mm.analyze_document('hello world', 'simplify', stream=True))
    assert isinstance(tokens, list)

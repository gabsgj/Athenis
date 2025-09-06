from app.models.model_manager import ModelManager
from app.utils.cache import Cache
import os

def test_stream_tokens_stub(monkeypatch):
    os.environ['FAST_TEST'] = '1'
    mm = ModelManager(cache=Cache())
    tokens = list(mm.stream_process('hello world', 'simplify', 'en'))
    assert isinstance(tokens, list)

import os
import json
from app.models.model_manager import ModelManager
from app.utils.cache import Cache

def test_process_shape():
    os.environ['EXTERNAL_LLM_API_URL'] = ''
    mm = ModelManager(cache=Cache())
    res = mm.process('This Agreement shall automatically renew every year unless terminated.', 'simplify', 'en')
    assert 'overview' in res
    assert 'plain_language' in res
    assert 'risks_detected' in res

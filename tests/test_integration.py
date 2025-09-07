import os
import json
from app.models.model_manager import ModelManager
from app.utils.cache import Cache

def test_process_shape():
    os.environ['EXTERNAL_LLM_API_URL'] = ''
    mm = ModelManager()
    res = mm.analyze_document('This Agreement shall automatically renew every year unless terminated.', 'simplify', stream=False)
    assert isinstance(res, str)
    assert len(res) > 0

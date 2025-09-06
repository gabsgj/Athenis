from app.utils.cache import Cache

def test_lru_cache():
    c = Cache()
    c.set('a', {'x':1})
    assert c.get('a')['x'] == 1

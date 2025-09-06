import os
import json
import time
from collections import OrderedDict
from typing import Any, Optional

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


class LRUCache:
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


class Cache:
    def __init__(self, redis_url: Optional[str] = None):
        self.client = None
        if redis_url and redis:
            try:
                self.client = redis.from_url(redis_url)
            except Exception:
                self.client = None
        self.lru = LRUCache(256)

    def get(self, key: str) -> Optional[Any]:
        if self.client:
            try:
                data = self.client.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        return self.lru.get(key)

    def set(self, key: str, value: Any, ttl: int = 3600):
        if self.client:
            try:
                self.client.setex(key, ttl, json.dumps(value))
                return
            except Exception:
                pass
        self.lru.set(key, value)

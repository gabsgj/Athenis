import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, rate_per_minute: int = 60):
        self.rate = rate_per_minute
        self.buckets = defaultdict(deque)
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # Clean up every 5 minutes

    def _cleanup_old_buckets(self):
        """Remove old buckets to prevent memory leaks"""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
            
        keys_to_remove = []
        for key, q in self.buckets.items():
            # Remove timestamps older than 2 minutes
            while q and now - q[0] > 120:
                q.popleft()
            # If bucket is empty, mark for removal
            if not q:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]
            
        self.last_cleanup = now

    def allow(self, key: str) -> bool:
        self._cleanup_old_buckets()
        
        now = time.time()
        window = 60
        q = self.buckets[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) < self.rate:
            q.append(now)
            return True
        return False

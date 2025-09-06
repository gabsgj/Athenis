import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, rate_per_minute: int = 60):
        self.rate = rate_per_minute
        self.buckets = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window = 60
        q = self.buckets[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) < self.rate:
            q.append(now)
            return True
        return False

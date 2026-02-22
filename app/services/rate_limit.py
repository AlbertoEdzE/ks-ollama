from time import time
from typing import Dict, Tuple
from app.config import settings

class RateLimiter:
    def __init__(self, rate_per_minute: int | None = None):
        self.rate = rate_per_minute or settings.rate_limit_per_minute
        self.buckets: Dict[str, Tuple[int, float]] = {}

    def allow(self, key: str) -> Tuple[bool, int, int]:
        now = time()
        window = 60
        limit = self.rate
        count, start = self.buckets.get(key, (0, now))
        if now - start >= window:
            count, start = 0, now
        if count < limit:
            count += 1
            self.buckets[key] = (count, start)
            remaining = limit - count
            reset = int(window - (now - start))
            return True, remaining, reset
        remaining = 0
        reset = int(window - (now - start))
        self.buckets[key] = (count, start)
        return False, remaining, reset

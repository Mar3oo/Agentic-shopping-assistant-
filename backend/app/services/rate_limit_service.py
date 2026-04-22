import math
import time
from collections import deque
from threading import Lock

_BUCKETS: dict[str, deque[float]] = {}
_LOCK = Lock()


class RateLimitExceeded(Exception):
    def __init__(self, message: str, limit: int, retry_after_seconds: int):
        self.payload = {
            "message": message,
            "limit": limit,
            "retry_after_seconds": retry_after_seconds,
        }
        super().__init__(message)


def enforce_rate_limit(
    user_id: str | None,
    scope: str,
    limit: int,
    window_seconds: int = 60,
    bucket_key: str | None = None,
) -> None:
    identity = user_id or bucket_key or "anonymous"
    bucket_key = f"{scope}:{identity}"
    now = time.time()

    with _LOCK:
        bucket = _BUCKETS.setdefault(bucket_key, deque())
        cutoff = now - window_seconds

        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            retry_after = max(1, math.ceil(window_seconds - (now - bucket[0])))
            raise RateLimitExceeded("Rate limit exceeded", limit, retry_after)

        bucket.append(now)

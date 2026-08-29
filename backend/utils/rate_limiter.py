"""Lightweight in-process rate limiting for brute-force-sensitive endpoints.

Process-local by design, matching this deployment's existing InMemoryCache
(backend/utils/cache.py) — safe because the production startup command is
pinned to a single worker (see Dockerfile / Procfile: `--workers 1`). This is
NOT suitable for a multi-replica or multi-worker deployment (each process
would track its own counters independently); that would need a shared store
such as Redis, which is explicitly out of scope for this pass.
"""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Request

from backend.exceptions.base import RateLimitExceededException


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, scope: str, max_attempts: int, window_seconds: float) -> None:
        """Raise RateLimitExceededException if `key` has exceeded `max_attempts`
        within the trailing `window_seconds` for the given `scope`."""
        now = time.time()
        bucket_key = (scope, key)
        with self._lock:
            hits = self._hits[bucket_key]
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= max_attempts:
                raise RateLimitExceededException()
            hits.append(now)

    def reset(self) -> None:
        """Clear all tracked state. Intended for test isolation."""
        with self._lock:
            self._hits.clear()


rate_limiter = InMemoryRateLimiter()

# Deliberately generous enough not to interfere with normal usage (a user
# mistyping a password a couple of times, or a test suite exercising the
# endpoint) while still bounding sustained brute-force/credential-stuffing
# attempts from a single client.
LOGIN_MAX_ATTEMPTS = 10
LOGIN_WINDOW_SECONDS = 30
REGISTER_MAX_ATTEMPTS = 5
REGISTER_WINDOW_SECONDS = 60


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce_login_rate_limit(request: Request) -> None:
    rate_limiter.check(_client_key(request), "login", LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_SECONDS)


def enforce_register_rate_limit(request: Request) -> None:
    rate_limiter.check(_client_key(request), "register", REGISTER_MAX_ATTEMPTS, REGISTER_WINDOW_SECONDS)

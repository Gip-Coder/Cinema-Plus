import time
import fnmatch
from typing import Dict, Any, Tuple, Optional

class InMemoryCache:
    """
    Decoupled Redis-ready Cache abstraction. 
    Can be replaced with a Redis-backed implementation in the future without 
    modifying routing logic.
    """
    def __init__(self, version: str = "v1"):
        # Maps key -> (expiry, data)
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.version = version

    def _make_key(self, key: str) -> str:
        """Appends the version namespace to the key if not already present."""
        if not key.endswith(f":{self.version}"):
            return f"{key}:{self.version}"
        return key

    def get(self, key: str) -> Optional[Any]:
        """Retrieve data from the cache. Returns None if key is expired or missing."""
        versioned_key = self._make_key(key)
        if versioned_key in self._cache:
            expiry, data = self._cache[versioned_key]
            if time.time() < expiry:
                return data
            else:
                del self._cache[versioned_key]
        return None

    def set(self, key: str, data: Any, ttl: int = 60):
        """Store data in the cache with a Time-To-Live (TTL) in seconds."""
        versioned_key = self._make_key(key)
        self._cache[versioned_key] = (time.time() + ttl, data)

    def invalidate(self, pattern: str):
        """Invalidate all keys matching the standard wildcard pattern (e.g. 'movie:*')."""
        versioned_pattern = self._make_key(pattern)
        keys_to_delete = []
        for key in list(self._cache.keys()):
            if fnmatch.fnmatch(key, versioned_pattern):
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self._cache[key]
            
    def clear(self):
        """Clears all cached elements."""
        self._cache.clear()

# Global cache instance
cache = InMemoryCache(version="v1")

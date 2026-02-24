"""
Simple TTL-based in-memory cache for dashboard endpoints.
No external dependencies required.
Thread-safe using dictionary.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
import logging

logger = logging.getLogger(__name__)


class TTLCache:
    """Simple TTL cache with auto-expiry"""
    
    def __init__(self):
        self._cache: Dict[str, dict] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.utcnow() > entry["expires_at"]:
            # Expired, remove and return None
            del self._cache[key]
            logger.debug(f"Cache expired for key: {key}")
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Set value in cache with TTL"""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }
        logger.debug(f"Cache set for key: {key}, TTL: {ttl_seconds}s")
    
    def clear(self, key: Optional[str] = None) -> None:
        """Clear specific key or entire cache"""
        if key:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache cleared for key: {key}")
        else:
            self._cache.clear()
            logger.debug("Cache fully cleared")
    
    def cleanup_expired(self) -> None:
        """Remove all expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry["expires_at"]
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
_cache = TTLCache()


def get_cache() -> TTLCache:
    """Get global cache instance"""
    return _cache


def cached(ttl_seconds: int = 60):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(ttl_seconds=60)
        def get_data(param1):
            return expensive_computation(param1)
    
    Args:
        ttl_seconds: Time to live for cache entry
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            cache = get_cache()
            
            # Generate cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            try:
                # Compute and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl_seconds)
                return result
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {str(e)}")
                # Return None on error, don't cache failure
                raise
        
        return wrapper
    
    return decorator

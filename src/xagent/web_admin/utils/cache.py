"""
Cache Module

This module provides caching functionality for frequently accessed data.
Implements a simple in-memory cache with TTL (Time To Live) support.
"""

import time
import logging
from typing import Any, Optional, Dict, Callable
from functools import wraps
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support"""
    
    def __init__(self, value: Any, ttl: int):
        """Initialize cache entry
        
        Args:
            value: Cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.expires_at = time.time() + ttl if ttl > 0 else float('inf')
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired
        
        Returns:
            True if expired, False otherwise
        """
        return time.time() > self.expires_at


class SimpleCache:
    """Simple in-memory cache with TTL support
    
    Thread-safe cache implementation for storing frequently accessed data.
    """
    
    def __init__(self, default_ttl: int = 300):
        """Initialize cache
        
        Args:
            default_ttl: Default time to live in seconds (default: 300 = 5 minutes)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    self._hits += 1
                    logger.debug(f"Cache hit: {key}")
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]
                    logger.debug(f"Cache expired: {key}")
            
            self._misses += 1
            logger.debug(f"Cache miss: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default_ttl if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> None:
        """Delete value from cache
        
        Args:
            key: Cache key
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache keys matching pattern
        
        Args:
            pattern: Pattern to match (simple substring match)
            
        Returns:
            Number of keys invalidated
        """
        with self._lock:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
            
            if keys_to_delete:
                logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")
            
            return len(keys_to_delete)
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'total_requests': total_requests
            }


def cached(cache: SimpleCache, key_func: Callable = None, ttl: Optional[int] = None):
    """Decorator for caching function results
    
    Args:
        cache: Cache instance to use
        key_func: Function to generate cache key from function arguments
                 If None, uses function name and str(args)
        ttl: Time to live in seconds (uses cache default if None)
    
    Example:
        @cached(my_cache, key_func=lambda session_id: f"config:{session_id}", ttl=300)
        def get_config(session_id):
            # expensive operation
            return config
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key: function name + args
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

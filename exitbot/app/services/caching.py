"""
Simple caching utilities for the application
"""
import functools
import time
import hashlib
import json
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

from exitbot.app.core.logging import get_logger

logger = get_logger("services.caching")

# Type variable for function return type
T = TypeVar("T")

# Simple in-memory cache
_cache: Dict[str, Tuple[Any, float]] = {}

# Cache settings
DEFAULT_TTL = 300  # 5 minutes in seconds
MAX_CACHE_ITEMS = 100  # Maximum number of items to store in cache


def cache_key(func_name: str, *args, **kwargs) -> str:
    """Generate a unique cache key based on function name and arguments."""
    # Create a string representation of args and kwargs
    args_str = json.dumps(args, sort_keys=True, default=str)
    kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)

    # Create hash of the combined string
    key = hashlib.md5(f"{func_name}:{args_str}:{kwargs_str}".encode()).hexdigest()
    return key


def ttl_cache(ttl: int = 300):
    """
    Decorator for time-based caching of function results

    Args:
        ttl: Time to live in seconds (default: 5 minutes)

    Returns:
        Decorated function
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            # Skip the first argument (usually 'self' or 'db')
            cache_key = f"{func.__name__}:{str(args[1:])}{str(kwargs)}"

            # Check if result is in cache and not expired
            if cache_key in _cache:
                result, expiry = _cache[cache_key]
                if expiry > time.time():
                    return result

            # Call the function and cache the result
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, time.time() + ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: Optional[str] = None):
    """
    Invalidate cached results

    Args:
        prefix: Optional prefix to match cache keys
    """
    global _cache

    if prefix:
        # Remove entries that start with the prefix
        _cache = {k: v for k, v in _cache.items() if not k.startswith(prefix)}
    else:
        # Clear the entire cache
        _cache = {}

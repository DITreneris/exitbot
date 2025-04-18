"""
LLM response caching utilities
"""
import functools
import time
import hashlib
from typing import Any, Callable, Dict, Tuple
import threading

from exitbot.app.core.logging import get_logger

logger = get_logger("exitbot.app.llm.cache")

# Simple in-memory cache for LLM responses
_cache: Dict[str, Tuple[Any, float]] = {}
# Locks for managing concurrent access to specific cache keys
_key_locks: Dict[str, threading.Lock] = {}
# Lock to protect access to the _key_locks dictionary itself
_locks_dict_lock = threading.Lock()

# Cache settings
DEFAULT_TTL = 600  # 10 minutes in seconds
MAX_CACHE_ITEMS = 100  # Maximum number of items to store in cache

def cached_llm_response(func: Callable) -> Callable:
    """
    Decorator to cache LLM responses to avoid unnecessary API calls
    
    Args:
        func: The function to cache
        
    Returns:
        Wrapped function with caching
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract prompt from keyword arguments ONLY
        prompt = kwargs.get("prompt")

        # Ensure prompt is a string for hashing
        prompt_str = ""
        if isinstance(prompt, str):
            prompt_str = prompt
        else:
            # Log a warning if prompt is not found or not a string
            logger.warning(f"Cache decorator expects 'prompt' keyword argument of type str, but got {type(prompt)}. Using empty string for cache key. Args: {args}, Kwargs: {kwargs}")
            # Depending on requirements, could raise TypeError("Cache decorator requires 'prompt' keyword argument of type str")

        # Generate a cache key based on prompt string
        key = hashlib.md5(prompt_str.encode()).hexdigest()
        
        # Check if value exists in cache and is not expired
        current_time = time.time()
        if key in _cache:
            value, expiry = _cache[key]
            if expiry > current_time:
                logger.debug(f"Cache hit for LLM response (key: {key[:6]}...)")
                return value
            else:
                # Cache exists but expired
                logger.debug(f"Cache expired for LLM response (key: {key[:6]}...)")
                # Don't delete yet, let the lock mechanism handle re-computation

        # Cache miss or expired - acquire lock for this key
        with _locks_dict_lock: # Protect access to _key_locks dict
            key_lock = _key_locks.setdefault(key, threading.Lock())

        logger.debug(f"Acquiring lock for key {key[:6]}...")
        with key_lock:
            logger.debug(f"Lock acquired for key {key[:6]}...")
            # --- Re-check cache inside the lock --- #
            # Another thread might have computed it while we waited for the lock
            if key in _cache:
                value, expiry = _cache[key]
                if expiry > time.time(): # Check expiry again
                    logger.debug(f"Cache hit after acquiring lock (key: {key[:6]}...)")
                    return value
                else:
                     logger.debug(f"Cache expired after acquiring lock (key: {key[:6]}...), recomputing.")
                     # Proceed to compute
            else:
                logger.debug(f"Cache still empty after acquiring lock (key: {key[:6]}...), computing.")
                # Proceed to compute

            # --- Call the original function --- # 
            logger.debug(f"Calling original function for key {key[:6]}...")
            result = func(*args, **kwargs)
            
            # --- Store result in cache --- #
            current_time = time.time() # Get fresh time
            _cache[key] = (result, current_time + DEFAULT_TTL)
            logger.debug(f"Stored result in cache for key {key[:6]}...)")
            
            # --- Cache pruning (moved inside lock?) --- #
            # Consider if pruning needs locking - maybe not critical if slightly over limit briefly
            if len(_cache) > MAX_CACHE_ITEMS:
                # Sort by expiry time and remove oldest entries
                sorted_items = sorted(_cache.items(), key=lambda x: x[1][1])
                items_to_remove = len(_cache) - MAX_CACHE_ITEMS
                if items_to_remove > 0:
                    logger.debug(f"Cache limit ({MAX_CACHE_ITEMS}) exceeded. Pruning {items_to_remove} items.")
                    removed_keys = []
                    for k, _ in sorted_items[:items_to_remove]:
                        # Also remove associated lock if it exists
                        # Acquire dict lock briefly to remove key lock
                        with _locks_dict_lock:
                            if k in _key_locks:
                                # Potentially unsafe if another thread is using this lock?
                                # For now, let's just remove the entry. A waiting thread might create it again.
                                del _key_locks[k]
                        del _cache[k]
                        removed_keys.append(k[:6] + "...")
                    logger.debug(f"Cache pruned. Removed keys: {removed_keys}")

            # Return the computed result
            return result
        # Lock automatically released here
    
    return wrapper 
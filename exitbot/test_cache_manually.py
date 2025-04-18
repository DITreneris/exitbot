"""
Manual test for the LLM Cache functionality
"""
import sys
import time
import pytest
from unittest.mock import MagicMock, patch, Mock, AsyncMock, call
from concurrent.futures import ThreadPoolExecutor
import unittest.mock

# Global counter for mock calls
call_counter = 0

# Import the decorator, not a non-existent class
from exitbot.app.llm.cache import cached_llm_response, _cache, DEFAULT_TTL, MAX_CACHE_ITEMS

# Mock function to simulate an LLM call
def mock_llm_call(prompt: str) -> dict:
    """Simulates an LLM call with a delay and increments counter"""
    global call_counter
    call_counter += 1
    print(f"Original mock_llm_call executing for prompt: {prompt}. Count: {call_counter}") # Debug print
    time.sleep(0.1) # Simulate network latency
    return {"response": f"Response to: {prompt}"}

# Apply the decorator to the mock function
cached_mock_llm_call = cached_llm_response(mock_llm_call)

@pytest.fixture(autouse=True)
def clear_cache_before_each_test():
    """Ensures the cache is empty before each test runs"""
    _cache.clear()
    yield
    _cache.clear()

def test_cache_hit():
    """Test that a subsequent identical call hits the cache"""
    prompt = "Test prompt 1"
    
    # First call (should not be cached)
    start_time = time.time()
    response1 = cached_mock_llm_call(prompt=prompt)
    duration1 = time.time() - start_time
    
    # Second call (should be cached)
    start_time = time.time()
    response2 = cached_mock_llm_call(prompt=prompt)
    duration2 = time.time() - start_time
    
    assert response1 == response2
    assert duration2 < duration1 / 2 # Cached call should be much faster
    assert len(_cache) == 1

def test_cache_miss_different_prompt():
    """Test that different prompts result in cache misses"""
    prompt1 = "Test prompt A"
    prompt2 = "Test prompt B"
    
    response1 = cached_mock_llm_call(prompt=prompt1)
    response2 = cached_mock_llm_call(prompt=prompt2)
    
    assert response1 != response2
    assert len(_cache) == 2

def test_cache_expiry():
    """Test that cache entries expire after TTL"""
    prompt = "Expiring prompt"
    ttl = 0.1 # Short TTL for testing
    
    original_ttl = DEFAULT_TTL
    try:
        # Temporarily change TTL for this test
        # Directly modifying module variable - use carefully
        import exitbot.app.llm.cache
        exitbot.app.llm.cache.DEFAULT_TTL = ttl

        # Call to cache the response
        cached_mock_llm_call(prompt=prompt)
        assert len(_cache) == 1

        # Wait for TTL to expire
        time.sleep(ttl * 1.1)

        # Call again - should be a cache miss
        start_time = time.time()
        cached_mock_llm_call(prompt=prompt)
        duration = time.time() - start_time
        
        # Check if it was a cache miss (took time)
        assert duration > 0.05 # Should be longer than a simple cache lookup
        assert len(_cache) == 1 # Cache should have been updated with new expiry

    finally:
        # Restore original TTL
        exitbot.app.llm.cache.DEFAULT_TTL = original_ttl

def test_cache_max_items():
    """Test that the cache size limit is enforced"""
    original_max = MAX_CACHE_ITEMS
    try:
        # Set a small max size for testing
        import exitbot.app.llm.cache
        exitbot.app.llm.cache.MAX_CACHE_ITEMS = 2

        # Fill the cache
        cached_mock_llm_call(prompt="Prompt 1")
        cached_mock_llm_call(prompt="Prompt 2")
        assert len(_cache) == 2

        # Add another item, triggering pruning
        cached_mock_llm_call(prompt="Prompt 3")
        assert len(_cache) == 2 # Should still be 2 due to pruning

        # Check which items remain (implementation dependent, but should be the latest 2)
        keys = list(_cache.keys())
        # Hashing makes order unpredictable, just check size

    finally:
        exitbot.app.llm.cache.MAX_CACHE_ITEMS = original_max

def test_concurrent_cache_access():
    """Test that concurrent access correctly uses the cache, calling the underlying function only once."""
    global call_counter
    call_counter = 0 # Reset counter before test
    _cache.clear() # Ensure cache is empty (fixture should do this, but belts and suspenders)

    prompt = "Concurrent Test Prompt"
    expected_result = {"response": f"Response to: {prompt}"}

    # No patching needed now, we check the counter

    def task():
        # Call the *globally decorated* function
        return cached_mock_llm_call(prompt=prompt)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(task) for _ in range(10)]
        results = [future.result() for future in futures]

    # Verify the underlying function was called exactly once via the counter
    try:
        assert call_counter == 1, f"Expected original mock_llm_call to be called once. Called {call_counter} times. Cache state: {_cache}"
        # Verify all results match the expected result
        for result in results:
            assert result == expected_result, f"Result {result} does not match expected {expected_result}"
    except AssertionError as e:
        print(f"AssertionError on call count/results: {e}")
        # No call_args_list to print now
        raise

def main():
    """Main function to run tests"""
    try:
        print("Starting manual LLM cache tests...")
        
        test_cache_hit()
        test_cache_miss_different_prompt()
        test_cache_expiry()
        test_cache_max_items()
        test_concurrent_cache_access()
        
        print("\nAll tests completed successfully!")
        return 0
    
    except Exception as e:
        print(f"Error during tests: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
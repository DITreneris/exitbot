"""
Tests for the circuit breaker functionality in the BaseLLMClient
"""
import time
from unittest.mock import patch

from exitbot.app.llm.client_base import BaseLLMClient, CircuitBreaker
from exitbot.app.llm.groq_client import GroqClient


class TestCircuitBreaker:
    """Test cases for the CircuitBreaker class"""

    def test_initial_state(self):
        """Test that circuit breaker initializes in closed state"""
        cb = CircuitBreaker(failure_threshold=5, recovery_time=60)

        assert cb.failure_count == 0
        assert cb.is_open is False
        assert cb.can_execute() is True

    def test_open_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, recovery_time=60)

        # Record failures
        cb.record_failure()
        assert cb.is_open is False  # Still closed

        cb.record_failure()
        assert cb.is_open is False  # Still closed

        cb.record_failure()
        assert cb.is_open is True  # Now open
        assert cb.can_execute() is False  # Can't execute when open

    def test_reset_after_success(self):
        """Test circuit breaker resets after success"""
        cb = CircuitBreaker(failure_threshold=3, recovery_time=60)

        # Record failures but not enough to open
        cb.record_failure()
        cb.record_failure()

        # Record success should reset count
        cb.record_success()
        assert cb.failure_count == 0

        # Circuit should be closed
        assert cb.is_open is False
        assert cb.can_execute() is True

    def test_half_open_after_recovery_time(self):
        """Test circuit allows a test request after recovery time"""
        cb = CircuitBreaker(
            failure_threshold=3, recovery_time=2
        )  # Short recovery for testing

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.is_open is True
        assert cb.can_execute() is False

        # Wait for recovery time
        time.sleep(2)

        # Should allow a test request
        assert cb.can_execute() is True

        # If the test request succeeds, circuit closes
        cb.record_success()
        assert cb.is_open is False
        assert cb.failure_count == 0


class TestCircuitBreakerIntegration:
    """Test the integration of CircuitBreaker with BaseLLMClient"""

    class _MockLLMClient(BaseLLMClient):
        """Mock implementation of BaseLLMClient for testing"""

        def __init__(self, should_fail=False, **kwargs):
            super().__init__(**kwargs)
            self.should_fail = should_fail
            self.call_count = 0

        def _send_request(self, prompt):
            """Mock implementation that can be configured to fail"""
            self.call_count += 1
            if self.should_fail:
                raise Exception("Simulated API failure")
            return {"response": "Success response"}

        def analyze_sentiment(self, text: str) -> float:
            """Mock implementation of analyze_sentiment"""
            return 0.0  # Simple mock implementation

    def test_client_uses_circuit_breaker(self):
        """Test that client uses circuit breaker to block requests after failures"""
        # Create client with threshold=2
        cb = CircuitBreaker(failure_threshold=2, recovery_time=60)
        client = self._MockLLMClient(
            should_fail=True,
            max_retries=1,  # Each call results in 1 failure recorded
            circuit_breaker=cb,
        )

        # First failing call -> failure_count = 1
        response1 = client.generate_response(prompt="Test prompt 1")
        assert "error" in response1
        assert client.circuit_breaker.failure_count == 1
        assert client.circuit_breaker.is_open is False  # Not open yet

        # Second failing call -> failure_count = 2, Circuit opens
        response2 = client.generate_response(prompt="Test prompt 2")
        assert "error" in response2
        assert client.circuit_breaker.failure_count == 2
        assert client.circuit_breaker.is_open is True  # Should be open now

        # Third call should be blocked by the open circuit breaker.
        initial_call_count = client.call_count  # Record call count AFTER second call
        response3 = client.generate_response(prompt="Test prompt 3")
        assert "error" in response3
        # Check the specific error message for circuit breaker
        assert response3["error"] == "Circuit breaker open"
        assert (
            client.call_count == initial_call_count
        )  # _send_request should not have been called

    def test_circuit_recovery(self):
        """Test that circuit closes after a successful request during half-open state"""
        # Create client with threshold=2, recovery=1
        cb = CircuitBreaker(failure_threshold=2, recovery_time=1)
        client = self._MockLLMClient(
            should_fail=True, max_retries=1, circuit_breaker=cb
        )

        # Make two failing calls to open the circuit
        client.generate_response(prompt="Fail 1")
        client.generate_response(prompt="Fail 2")
        assert client.circuit_breaker.is_open is True  # Circuit is open

        # Wait for recovery time
        time.sleep(1.5)

        # Switch client to succeed
        client.should_fail = False

        # Make a call during the half-open state - it should succeed
        response_success = client.generate_response(prompt="Success attempt")
        assert "error" not in response_success  # Should succeed
        assert response_success["response"] == "Success response"

        # Check that the circuit is now closed after success
        assert client.circuit_breaker.is_open is False
        assert client.circuit_breaker.failure_count == 0  # Failure count reset

        # Subsequent calls should also succeed
        response_subsequent = client.generate_response(prompt="Subsequent success")
        assert "error" not in response_subsequent


class TestGroqClientWithCircuitBreaker:
    """Test the GroqClient with circuit breaker implementation"""

    @patch("exitbot.app.llm.groq_client.requests.post")
    def test_groq_client_circuit_breaker(self, mock_post):
        """Test GroqClient properly uses circuit breaker on API failures"""
        # Configure mock to fail consistently
        mock_post.side_effect = Exception("API timeout for groq circuit breaker test")

        # Create client with threshold=2
        cb = CircuitBreaker(failure_threshold=2, recovery_time=60)
        client = GroqClient(
            api_key="test-key-cb",  # Slightly unique key just in case
            model="test-model-cb",
            max_retries=1,  # Each call records 1 failure
        )
        client.circuit_breaker = cb  # Replace the default breaker

        # Use unique prompts for this test
        prompt1 = "Unique prompt for Groq CB test - call 1"
        prompt2 = "Unique prompt for Groq CB test - call 2"
        prompt3 = "Unique prompt for Groq CB test - call 3"

        # First failing call -> failure_count = 1
        response1 = client.generate_response(prompt=prompt1)
        assert "error" in response1
        assert client.circuit_breaker.failure_count == 1
        assert client.circuit_breaker.is_open is False  # Not open yet

        # Second failing call -> failure_count = 2, Circuit opens
        response2 = client.generate_response(prompt=prompt2)
        assert "error" in response2
        assert client.circuit_breaker.failure_count == 2
        assert client.circuit_breaker.is_open is True  # Should be open now

        # Third call should be blocked by circuit breaker
        mock_post.reset_mock()  # Reset mock call count BEFORE the blocked call
        response3 = client.generate_response(prompt=prompt3)
        assert "error" in response3
        assert response3["error"] == "Circuit breaker open"
        mock_post.assert_not_called()  # API should not have been called

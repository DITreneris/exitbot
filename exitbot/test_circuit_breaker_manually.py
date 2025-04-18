"""
Manual test for the CircuitBreaker functionality
"""
import time
from exitbot.app.llm.client_base import CircuitBreaker

class _TestService:
    """Simple service to test circuit breaker"""
    
    def __init__(self):
        self.fail_count = 0
        self.success_count = 0
        
    def reset(self):
        """Reset counters"""
        self.fail_count = 0
        self.success_count = 0
        
    def call_api(self, fail=False):
        """Simulate API call with optional failure"""
        if fail:
            self.fail_count += 1
            raise Exception("Simulated API failure")
        else:
            self.success_count += 1
            return "API call succeeded"
            
def test_circuit_breaker():
    """Test circuit breaker operation"""
    print("\n===== Testing CircuitBreaker =====")
    
    # Create test service
    service = _TestService()
    
    # Create circuit breaker with low thresholds for testing
    breaker = CircuitBreaker(failure_threshold=3, recovery_time=2)
    
    # Test normal operation (closed state)
    print("\nInitial state (CLOSED):")
    for i in range(5):
        if breaker.can_execute():
            try:
                result = service.call_api()
                breaker.record_success()
                print(f"Call {i+1} succeeded: {result}")
            except Exception as e:
                breaker.record_failure()
                print(f"Call {i+1} failed: {str(e)}")
        else:
            print(f"Call {i+1} rejected: Circuit open")
    
    # Test failure handling
    print("\nFailure handling:")
    for i in range(5):
        if breaker.can_execute():
            try:
                # Simulate failure
                result = service.call_api(fail=True)
                breaker.record_success()
                print(f"Call {i+1} succeeded: {result}")
            except Exception as e:
                breaker.record_failure()
                print(f"Call {i+1} failed: {str(e)}")
        else:
            print(f"Call {i+1} rejected: Circuit open")
            
    # Verify circuit opened
    print(f"\nCircuit state - Is open: {breaker.is_open}")
    print(f"Service counters - Success: {service.success_count}, Fail: {service.fail_count}")
    
    # Test circuit open rejection
    print("\nCircuit OPEN, calls should be rejected:")
    for i in range(3):
        if breaker.can_execute():
            try:
                result = service.call_api()
                breaker.record_success()
                print(f"Call {i+1} succeeded: {result}")
            except Exception as e:
                breaker.record_failure()
                print(f"Call {i+1} failed: {str(e)}")
        else:
            print(f"Call {i+1} rejected: Circuit open")
    
    # Wait for recovery timeout
    print("\nWaiting for recovery timeout...")
    time.sleep(3)
    
    # Test half-open state
    print("\nCircuit should be HALF_OPEN (allowing test request):")
    print(f"Circuit is open: {breaker.is_open}")
    print(f"Can execute: {breaker.can_execute()}")
    
    # Test successful recovery
    if breaker.can_execute():
        try:
            result = service.call_api()
            breaker.record_success()
            print(f"Recovery succeeded: {result}")
        except Exception as e:
            breaker.record_failure()
            print(f"Recovery failed: {str(e)}")
    else:
        print("Recovery rejected: Circuit still open")
        
    # Verify circuit closed again
    print(f"\nFinal circuit state - Is open: {breaker.is_open}")
    print(f"Service counters - Success: {service.success_count}, Fail: {service.fail_count}")
    
    print("\nCircuit breaker test completed")

if __name__ == "__main__":
    test_circuit_breaker() 
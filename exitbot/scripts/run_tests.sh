#!/bin/bash

# Run all tests to verify deployment readiness
echo "Starting deployment readiness tests..."

# Set testing environment
export ENVIRONMENT=testing
export TESTING=1

# Create the test reports directory
mkdir -p ../test-reports

# Function to run tests and log results
run_test() {
    echo "Running $1 tests..."
    python -m pytest ../tests/$2 -v --junitxml=../test-reports/$3.xml
    
    if [ $? -eq 0 ]; then
        echo "✅ $1 tests passed"
        return 0
    else
        echo "❌ $1 tests failed"
        return 1
    fi
}

# Track overall test status
test_status=0

# Run API endpoint tests
run_test "API endpoint" "test_api_endpoints.py" "api_endpoints"
api_status=$?
test_status=$((test_status + api_status))

# Run authentication tests
run_test "Authentication" "test_auth.py" "auth"
auth_status=$?
test_status=$((test_status + auth_status))

# Run LLM integration tests
run_test "LLM integration" "test_llm.py test_groq_integration.py" "llm_integration"
llm_status=$?
test_status=$((test_status + llm_status))

# Run performance tests
run_test "Performance" "test_performance.py" "performance"
perf_status=$?
test_status=$((test_status + perf_status))

# Run integration tests
run_test "Integration" "test_integration.py" "integration"
integration_status=$?
test_status=$((test_status + integration_status))

# Generate test summary report
echo -e "\n==== Test Summary ===="
echo "API Endpoint Tests: $([ $api_status -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Authentication Tests: $([ $auth_status -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "LLM Integration Tests: $([ $llm_status -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Performance Tests: $([ $perf_status -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "Integration Tests: $([ $integration_status -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
echo "======================="

# Provide overall status
if [ $test_status -eq 0 ]; then
    echo -e "\n✅ All tests passed! System is ready for deployment."
    exit 0
else
    echo -e "\n❌ Some tests failed. Please fix issues before proceeding with deployment."
    exit 1
fi 
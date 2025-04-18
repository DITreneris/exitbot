# Run all tests to verify deployment readiness
Write-Host "Starting deployment readiness tests..." -ForegroundColor Cyan

# Set testing environment
$env:ENVIRONMENT = "testing"
$env:TESTING = "1"

# Create the test reports directory
$testReportsDir = "..\test-reports"
if (-not (Test-Path -Path $testReportsDir)) {
    New-Item -ItemType Directory -Path $testReportsDir | Out-Null
}

# Function to run tests and log results
function Run-Test {
    param (
        [string]$TestName,
        [string]$TestPath,
        [string]$ReportName
    )
    
    Write-Host "Running $TestName tests..." -ForegroundColor Yellow
    python -m pytest ..\tests\$TestPath -v --junitxml=..\test-reports\$ReportName.xml
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ $TestName tests passed" -ForegroundColor Green
        return 0
    } else {
        Write-Host "❌ $TestName tests failed" -ForegroundColor Red
        return 1
    }
}

# Track overall test status
$testStatus = 0

# Run API endpoint tests
$apiStatus = Run-Test -TestName "API endpoint" -TestPath "test_api_endpoints.py" -ReportName "api_endpoints"
$testStatus += $apiStatus

# Run authentication tests
$authStatus = Run-Test -TestName "Authentication" -TestPath "test_auth.py" -ReportName "auth"
$testStatus += $authStatus

# Run LLM integration tests
$llmStatus = Run-Test -TestName "LLM integration" -TestPath "test_llm.py test_groq_integration.py" -ReportName "llm_integration"
$testStatus += $llmStatus

# Run performance tests
$perfStatus = Run-Test -TestName "Performance" -TestPath "test_performance.py" -ReportName "performance"
$testStatus += $perfStatus

# Run integration tests
$integrationStatus = Run-Test -TestName "Integration" -TestPath "test_integration.py" -ReportName "integration"
$testStatus += $integrationStatus

# Generate test summary report
Write-Host "`n==== Test Summary ====" -ForegroundColor Cyan
Write-Host "API Endpoint Tests: $(if ($apiStatus -eq 0) { "✅ PASS" } else { "❌ FAIL" })"
Write-Host "Authentication Tests: $(if ($authStatus -eq 0) { "✅ PASS" } else { "❌ FAIL" })"
Write-Host "LLM Integration Tests: $(if ($llmStatus -eq 0) { "✅ PASS" } else { "❌ FAIL" })"
Write-Host "Performance Tests: $(if ($perfStatus -eq 0) { "✅ PASS" } else { "❌ FAIL" })"
Write-Host "Integration Tests: $(if ($integrationStatus -eq 0) { "✅ PASS" } else { "❌ FAIL" })"
Write-Host "=======================" -ForegroundColor Cyan

# Provide overall status
if ($testStatus -eq 0) {
    Write-Host "`n✅ All tests passed! System is ready for deployment." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Some tests failed. Please fix issues before proceeding with deployment." -ForegroundColor Red
    exit 1
} 
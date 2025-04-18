#!/usr/bin/env python
"""
Test runner script for ExitBot application
Executes all tests and generates reports
"""
import os
import sys
import pytest
import argparse
import time
from datetime import datetime
from pathlib import Path

def main():
    """Main function to run tests with reporting"""
    parser = argparse.ArgumentParser(description="Run ExitBot tests with reporting")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--xml", action="store_true", help="Generate JUnit XML report")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--test-dir", default="tests", help="Test directory to run")
    parser.add_argument("--pattern", default="test_*.py", help="Test file pattern")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    args = parser.parse_args()

    # Create reports directory if it doesn't exist
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    pytest_args = ["-xvs"] if args.verbose else ["-xvs"]
    
    # Add report arguments
    if args.html:
        pytest_args.extend(["--html", f"{reports_dir}/report_{timestamp}.html"])
    
    if args.xml:
        pytest_args.extend(["--junitxml", f"{reports_dir}/report_{timestamp}.xml"])
    
    # Set test discovery pattern
    test_path = args.test_dir
    if args.pattern:
        test_path = f"{test_path}/{args.pattern}"
    
    # Add performance tests if requested
    if not args.performance:
        pytest_args.append("--ignore=tests/test_performance.py")
    
    # Run with or without coverage
    if args.coverage:
        pytest_args = [
            "--cov=app",
            "--cov-report", f"html:{reports_dir}/coverage_{timestamp}",
            "--cov-report", "term"
        ] + pytest_args
    
    # Add test directory to path
    pytest_args.append(test_path)
    
    print(f"Running tests with arguments: {' '.join(pytest_args)}")
    start_time = time.time()
    result = pytest.main(pytest_args)
    end_time = time.time()
    
    # Print summary
    print(f"\nTest run completed in {end_time - start_time:.2f} seconds")
    if args.html:
        print(f"HTML report generated at {reports_dir}/report_{timestamp}.html")
    if args.xml:
        print(f"XML report generated at {reports_dir}/report_{timestamp}.xml")
    if args.coverage:
        print(f"Coverage report generated at {reports_dir}/coverage_{timestamp}")
    
    return result

if __name__ == "__main__":
    sys.exit(main()) 
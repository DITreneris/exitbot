# ExitBot Tests

This directory contains integration tests for the ExitBot application. These tests verify that different components of the system work correctly together.

## Test Categories

- `test_auth.py`: Tests authentication and permission flows
- `test_interview.py`: Tests interview creation, message processing, and completion
- `test_reports.py`: Tests report generation and data export

## Running Tests

To run the tests, make sure you have pytest installed and then run:

```bash
# From the project root
pytest exitbot/tests/

# To run a specific test file
pytest exitbot/tests/test_auth.py

# To run with verbose output
pytest exitbot/tests/ -v

# To run with coverage reporting
pytest exitbot/tests/ --cov=exitbot
```

## Test Setup

The tests use an in-memory SQLite database, which is created freshly for each test. This ensures tests are isolated and can be run in any order.

Test fixtures in `conftest.py` provide:

- Database session
- Test client
- Test users (admin, HR, employee)
- Authentication tokens

## Adding New Tests

When adding new tests:

1. Use the appropriate test file based on what you're testing
2. Utilize the fixtures from `conftest.py`
3. Clean up any resources created during the test
4. Keep tests independent from each other

## Mocking

These integration tests use a real database but mock the Ollama API. The tests don't require Ollama to be running. 
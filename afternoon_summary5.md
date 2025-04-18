# Debugging Summary (Afternoon Session 5)

## Initial Problem

The primary focus was on fixing failing performance tests in `exitbot/tests/test_performance.py`, specifically:
- `test_standalone_interview_message_performance`: Failing with 404 Not Found when trying to `POST` to `/api/v1/interviews/{id}/message`.
- `test_interview_message_performance` & `test_report_generation_performance`: Also failing/skipped due to similar 404 issues.

## Debugging Steps & Findings

1.  **Direct Router Inclusion (`conftest.py`):** Attempted to fix 404s by explicitly including `auth`, `interviews`, and `reports` routers onto the global `app` within the `client` fixture in `conftest.py`. This initially led to `ModuleNotFoundError`s due to incorrect import paths, which were subsequently fixed.
2.  **`async`/`sync` Mismatch:** Investigated application startup. Found `main.py` was attempting to `await` the synchronous `init_db()` function within its `lifespan` manager. Corrected this by removing the `await` call. This fixed the startup `TypeError` but not the 404s.
3.  **Database Session / Override Investigation:**
    *   Confirmed that interviews created directly using the `test_db` session fixture *could* be retrieved within the test function itself using `crud.get_interview(db=test_db, ...)`.
    *   Verified the `client` fixture setup, `get_db` dependency, and `crud.get_interview` logic seemed correct.
    *   Refactored the `test_standalone_interview_message_performance` to create the interview via API calls (`client.post("/api/v1/interviews/")`) instead of direct DB manipulation, hoping to align the state better with the application context. This revealed the `POST /api/v1/interviews/` route itself was returning 404.
4.  **API Prefix Correction:** Discovered the root cause of the widespread 404s: `settings.API_V1_PREFIX` was defined as `/api` instead of the expected `/api/v1`. Corrected this in `exitbot/app/core/config.py`. This fixed the 404 for the base `/api/v1/interviews/` route but revealed a 403 Forbidden error during interview creation in the test.
5.  **Authentication Patch/Override:**
    *   Diagnosed the 403 error as a mismatch between the dependency used by the endpoint (`deps.get_current_active_user`) and the target used by the test's `@patch` decorator (`exitbot.app.auth.get_current_user`).
    *   Corrected the `@patch` target, but the 403 persisted.
    *   Tried temporarily setting the mocked user's `is_admin` flag to `True`, which also didn't resolve the 403, casting doubt on the patch effectiveness.
    *   Switched to using FastAPI's recommended `app.dependency_overrides` mechanism directly within the test function (`test_standalone_interview_message_performance`) to inject the `test_employee`. This **successfully resolved the 403 error**, allowing interview creation (201) and update (200).
6.  **Local App in `conftest.py`:** Tried isolating the `client` fixture by creating a local `FastAPI` app instance within it and adding only necessary routers. This **caused widespread test failures** across the suite because the client no longer used the fully configured global `app`.
7.  **Reverted `conftest.py`:** Reverted the `client` fixture to the standard approach: using the global `app` and applying only the DB dependency override.

## Current State

-   The `client` fixture in `conftest.py` uses the global `app` from `main.py` and correctly overrides the `get_db` dependency.
-   The `test_standalone_interview_message_performance` test:
    -   Successfully applies a dependency override for `get_current_active_user` within the test function.
    -   Successfully creates an interview via `POST /api/v1/interviews/` (Status 201).
    *   Successfully updates the interview status via `PUT /api/v1/interviews/1` (Status 200).
    *   **Still fails** with a **404 Not Found** when attempting `POST /api/v1/interviews/1/message`.

## Current Issues

1.  **Persistent 404 on `/message` Route:** The primary blocking issue is that the `POST /api/v1/interviews/{id}/message` route is not found by `TestClient`, despite the base `/api/v1/interviews/` routes working correctly within the same test and the route definition appearing correct.
2.  **Other Performance Tests:** The other performance tests (`test_interview_message_performance`, `test_report_generation_performance`) are likely still failing/skipped due to related routing or setup issues that haven't been addressed yet.

## Future Steps

1.  **Diagnose `/message` 404:** Focus on why `POST /api/v1/interviews/{id}/message` fails.
    *   Add detailed logging within the `interviews.router` definition and the `send_message` endpoint itself.
    *   Inspect the `app.routes` or `client.app.routes` *just before* the failing API call in the test to see if the route is listed correctly.
    *   Consider potential interactions with path parameters (`{interview_id}`) in the `TestClient` context.
    *   Review the exact sequence of router inclusions (`main.py`, `api/__init__.py`, `api/api.py` - although `api.py` seems unused now) to ensure consistency and no conflicts.
2.  **Stabilize `client` Fixture:** Ensure the current `client` fixture setup (global app + DB override) allows the majority of *other* tests to pass, as indicated by previous runs before the "local app" detour. If the full suite run still shows many failures, investigate those regressions.
3.  **Address Skipped Tests:** Once the `/message` route is fixed, unskip and fix the remaining performance tests (`test_interview_message_performance`, `test_report_generation_performance`).

---

## Updates (Post-Summary 5)

1.  **Implemented Suggestions from `afternoon_summary5.md`:**
    *   Added a debug print statement in `test_standalone_interview_message_performance` to list registered routes containing "message" right before the failing API call.
    *   Added a centralized `autouse=True` fixture `override_auth` to `conftest.py` to handle `get_current_active_user` overrides for all tests (using `test_employee` by default).
    *   Removed the manual override logic from `test_standalone_interview_message_performance`.
    *   Removed the `@pytest.mark.skip` decorators from `test_interview_message_performance` and `test_report_generation_performance` (Note: their implementations are still `pass`).
    *   Updated the `client` fixture in `conftest.py` to initialize `TestClient` with `raise_server_exceptions=False`.
    *   Added a startup event handler (`log_registered_routes`) to `exitbot/app/main.py` to log routes on application startup.
2.  **Initial Test Run Error (`NameError`):** The first attempt to run the test after these changes failed due to a `NameError: name 'app' is not defined` in `main.py`. This was because the `@app.on_event("startup")` decorator for `log_registered_routes` was placed *before* the `app = FastAPI(...)` line.
3.  **`NameError` Fix:** Moved the `log_registered_routes` function and its decorator to *after* the `app = FastAPI(...)` definition in `main.py`.
4.  **Second Test Run Error (`ERROR: not found`):** The next attempt to run `pytest ...::test_standalone_interview_message_performance -s` failed with `ERROR: not found`. This was because the target test function is defined at the module level, not within a class, requiring a different pytest command.
5.  **Startup Logic Refactor (`lifespan`):** Refactored `main.py` to move all startup logic (DB init, Prometheus expose, route logging) into the `lifespan` context manager, removing the deprecated `@app.on_event("startup")` handlers.

## Current Blocker

-   **Need Test Output:** We need the output from running the **corrected pytest command:**
    ```bash
    pytest exitbot/tests/test_performance.py -s
    ```
    This output is required to see if the `/api/v1/interviews/{interview_id}/message` route is registered in the test client's app and to diagnose the persistent 404 error.

## Immediate Next Steps

1.  **Run the Test:** Execute `pytest exitbot/tests/test_performance.py -s` in the terminal.
2.  **Share Output:** Provide the full output from the test run.
3.  **Analyze Output:** Examine the output for the `DEBUG [...] Registered message routes:` line and any error messages to determine the cause of the 404.

## Subsequent Steps

1.  Fix the root cause of the 404 based on the analysis.
2.  Restore the original implementation logic for the `test_interview_message_performance` and `test_report_generation_performance` tests.
3.  Run the full test suite to check for regressions.

---

## Further Updates (Post-Summary 5)

6.  **Third Test Run Error (`SyntaxError: unmatched '['`):** The attempt to run `pytest exitbot/tests/test_performance.py -s` failed due to a syntax error in the debug print statement within `test_standalone_interview_message_performance`. The list comprehension was incorrectly embedded directly within the f-string.
7.  **Print Statement Fix:** Corrected the syntax error by evaluating the list comprehension into a variable *before* the print statement and using the variable in the f-string.
8.  **Fourth Test Run Error (`SyntaxError: expected 'except' or 'finally'`):** Running the test command again resulted in a syntax error at the end of `test_standalone_interview_message_performance`, before the `TestPerformance` class definition. This occurred because the `finally` block of a `try...finally` had been removed earlier (as part of removing manual overrides), but the `try` keyword remained.
9.  **`try` Block Fix:** Removed the now-redundant `try:` line from `test_standalone_interview_message_performance`.
10. **Fifth Test Run Analysis (404 Root Cause Found):** Running the tests again finally showed the `test_standalone_interview_message_performance` failing with a 404, but the logs revealed the root cause:
    *   Test was calling: `POST /api/v1/interviews/{id}/message`
    *   Router registered: `POST /api/v1/interviews/{id}/messages` (plural)
11. **Path Mismatch Fix:** Corrected the path in the `client.post` call within `test_standalone_interview_message_performance` to use `/messages`. This resulted in the test **PASSING**.
12. **New Failures (`AttributeError: 'TestClient' object has no attribute 'app'`)**: With the standalone test passing, new failures appeared in the tests within the `TestPerformance` class (`test_health_check_performance`, `test_health_check_load`, `test_interview_message_performance`, `test_report_generation_performance`, `test_api_throughput`). These were caused by the methods trying to use a global `client` instance instead of the `client` fixture.
13. **Client Fixture Fix:** Removed the global `client` instance from `test_performance.py` and modified the method signatures within the `TestPerformance` class to accept the `client` fixture as an argument.
14. **Prepare Skipped Tests for Restoration:** Removed the outdated `@patch` decorators and `pass` statements from `test_interview_message_performance` and `test_report_generation_performance`. Added temporary `pytest.skip` markers.

## Current Status

-   The primary 404 error on the message route is **resolved**. `test_standalone_interview_message_performance` passes.
-   Tests within the `TestPerformance` class should now be using the correct `client` fixture.
-   `test_interview_message_performance` and `test_report_generation_performance` are ready to have their original implementation logic restored (currently marked with `pytest.skip`).

## Immediate Next Steps

1.  **Find Original Code:** Locate the original implementation code for the `test_interview_message_performance` and `test_report_generation_performance` test functions.
2.  **Restore Implementation:** Insert the original code into the respective functions in `exitbot/tests/test_performance.py`, replacing the `pytest.skip(...)` lines.
3.  **Run Tests:** Execute `pytest exitbot/tests/test_performance.py -s` again.
4.  **Analyze Results:** Check if the restored tests pass or if they reveal new issues (e.g., needing specific admin authentication override for `test_report_generation_performance`). 
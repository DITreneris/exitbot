"""
E2E tests for the HR Streamlit application using Playwright.
Requires the Streamlit app to be running separately.
"""

import pytest
from playwright.sync_api import Page, expect

# Base URL for the Streamlit app
APP_URL = "http://localhost:8501"
# Credentials for testing (adjust if needed)
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "password"


@pytest.mark.e2e
def test_hr_app_login_logout(page: Page):
    """Tests the login and logout flow of the HR application."""

    page.goto(APP_URL)

    # --- Login ---

    # 1. Wait for the main Streamlit app container to ensure the page is loaded
    app_container = page.locator('div[data-testid="stAppViewContainer"]')
    expect(app_container).to_be_visible(
        timeout=30000
    )  # Wait for the main app container

    # 2. Find the form container directly using its data-testid
    form_container = app_container.locator('div[data-testid="stForm"]')
    expect(form_container).to_be_visible(timeout=10000)  # Wait for the form

    # Locate inputs and button using the selectors found during inspection
    email_input = form_container.locator('input[placeholder="admin@example.com"]')
    password_input = form_container.locator('input[type="password"]')
    # Use the specific data-testid for the submit button
    login_button = form_container.locator(
        'button[data-testid="baseButton-secondaryFormSubmit"]'
    )

    # Expect the login form elements to be visible
    expect(email_input).to_be_visible()
    expect(password_input).to_be_visible()
    expect(login_button).to_be_visible()

    # Fill the login form
    email_input.fill(TEST_EMAIL)
    password_input.fill(TEST_PASSWORD)

    # Click the login button
    login_button.click()

    # Add a small explicit wait to allow Streamlit state to settle after rerun
    page.wait_for_timeout(1000)

    # --- Verify Login Success ---

    # Wait for the Logout button in the sidebar (which is outside the form)
    # Locate it relative to the main app container or page
    logout_button = page.locator('button:has-text("Logout")')
    # Increase timeout significantly to allow for Streamlit rerun and rendering
    expect(logout_button).to_be_visible(timeout=30000)

    # Optionally, check if dashboard title is visible
    # expect(page.locator('h1:has-text("Dashboard")')).to_be_visible()

    # --- Logout ---

    logout_button.click()

    # --- Verify Logout Success ---

    # Wait for the main container first, then the form container
    expect(app_container).to_be_visible(timeout=10000)
    # Check the form container is visible again after logout
    expect(form_container).to_be_visible(timeout=10000)
    # Check specific elements within the form are visible again
    expect(email_input).to_be_visible()
    expect(login_button).to_be_visible()

    # Optionally, check that the logout button is no longer visible
    expect(logout_button).not_to_be_visible()

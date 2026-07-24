from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from app.browser.locator_resolver import resolve_locator

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)
page_url = html_file.as_uri()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )

    page = browser.new_page()
    page.goto(page_url)

    email_input = resolve_locator(
        page,
        locator_type="label",
        locator_value="Email",
    )

    email_input.fill("student@example.com")

    login_button = resolve_locator(
        page,
        locator_type="role",
        locator_value="button",
    )

    login_button.click()

    message = resolve_locator(
        page,
        locator_type="text",
        locator_value="Welcome to TestPilot!",
    )

    expect(message).to_be_visible()

    print("Locator resolver test passed.")

    browser.close()
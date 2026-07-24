from pathlib import Path

from playwright.sync_api import sync_playwright

from app.browser.step_executor import StepExecutor
from app.models.test_case import TestStep


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)

page_url = html_file.as_uri()


steps = [
    TestStep(
        step_number=1,
        description="Enter email address",
        action="fill",
        locator_type="label",
        locator_value="Email",
        input_value="student@example.com",
    ),
    TestStep(
        step_number=2,
        description="Enter password",
        action="fill",
        locator_type="placeholder",
        locator_value="Enter password",
        input_value="secret123",
    ),
    TestStep(
        step_number=3,
        description="Click sign-in button",
        action="click",
        locator_type="role",
        locator_value="button",
        locator_name="Sign in",
    ),
    TestStep(
        step_number=4,
        description="Verify welcome message",
        action="assert_text",
        locator_type="text",
        locator_value="Welcome to TestPilot!",
        expected_text="Welcome to TestPilot!",
    ),
    TestStep(
        step_number=5,
        description="Capture final screenshot",
        action="screenshot",
    ),
]


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )

    page = browser.new_page()
    page.goto(page_url)

    executor = StepExecutor()

    for step in steps:
        result = executor.execute(page, step)

        print(result.model_dump())

        if result.status == "failed":
            break

    browser.close()
from pathlib import Path

from playwright.sync_api import sync_playwright

from test_case_runner import TestCaseRunner
from app.models.test_case import TestCase, TestStep

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)
test_case = TestCase(
    name="Successful login test",
    objective="Verify that the login form displays a welcome message.",
    start_url=html_file.as_uri(),
    steps=[
        TestStep(
            step_number=1,
            description="Enter email",
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
            description="Click sign-in",
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
    ],
)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )

    runner = TestCaseRunner()

    result = runner.run(
        browser=browser,
        test_case=test_case,
    )

    print(result.model_dump_json(indent=2))

    browser.close()
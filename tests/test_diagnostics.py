from pathlib import Path

from playwright.sync_api import sync_playwright

from app.browser.test_case_runner import (
    TestCaseRunner as BrowserTestCaseRunner,
)
from app.models.test_case import (
    TestCase as BrowserTestCase,
    TestStep as BrowserTestStep,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "diagnostics_demo.html"
)


def test_browser_diagnostics():
    test_case = BrowserTestCase(
        name="Diagnostics test",
        objective="Capture browser errors.",
        start_url=html_file.as_uri(),
        steps=[
            BrowserTestStep(
                step_number=1,
                description="Capture page screenshot",
                action="screenshot",
            )
        ],
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        runner = BrowserTestCaseRunner()

        result = runner.run(
            browser=browser,
            test_case=test_case,
        )

        browser.close()

    print(result.model_dump_json(indent=2))

    assert result.status == "passed"

    assert any(
        "Demo console error" in error
        for error in result.diagnostics.console_errors
    )

    assert any(
        "Demo uncaught JavaScript error" in error
        for error in result.diagnostics.page_errors
    )
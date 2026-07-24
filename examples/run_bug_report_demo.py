import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from app.ai.bug_report_generator import (
    BugReportGenerator,
)
from app.browser.test_case_runner import (
    TestCaseRunner,
)
from app.models.test_case import (
    TestCase,
    TestStep,
)
from app.reporting.result_writer import ResultWriter


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "diagnostics_demo.html"
)

token = os.getenv("HF_TOKEN")
model_id = os.getenv("HF_MODEL")

if not token or not model_id:
    raise RuntimeError(
        "HF_TOKEN or HF_MODEL is missing from .env"
    )


test_case = TestCase(
    name="Browser diagnostics test",
    objective=(
        "Detect JavaScript and browser console errors."
    ),
    start_url=html_file.as_uri(),
    steps=[
        TestStep(
            step_number=1,
            description="Capture the diagnostics page",
            action="screenshot",
        )
    ],
)


runner = TestCaseRunner()
result_writer = ResultWriter()

bug_report_generator = BugReportGenerator(
    token=token,
    model_id=model_id,
)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True
    )

    result = runner.run(
        browser=browser,
        test_case=test_case,
    )

    browser.close()


print("\nTest result:")
print(result.model_dump_json(indent=2))

result_path = result_writer.write(result)

print(f"\nTest result saved to: {result_path}")


bug_report = bug_report_generator.generate(result)

if bug_report:
    run_directory = (
        PROJECT_ROOT
        / "artifacts"
        / "runs"
        / result.run_id
    )

    bug_report_path = (
        run_directory / "bug_report.json"
    )

    bug_report_path.write_text(
        bug_report.model_dump_json(indent=2),
        encoding="utf-8",
    )

    print("\nGenerated bug report:")
    print(bug_report.model_dump_json(indent=2))

    print(
        f"\nBug report saved to: "
        f"{bug_report_path}"
    )
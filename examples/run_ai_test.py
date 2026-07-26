import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from app.ai.bug_report_generator import (
    BugReportGenerator,
)
from app.ai.test_plan_generator import (
    TestPlanGenerator,
)
from app.services.test_orchestrator import (
    TestOrchestrator,
)


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)

page_url = html_file.as_uri()

objective = (
    "Test the login form and verify that signing "
    "in displays the welcome message."
)

token = os.getenv("HF_TOKEN")
model_id = os.getenv("HF_MODEL")

if not token or not model_id:
    raise RuntimeError(
        "HF_TOKEN or HF_MODEL is missing from .env"
    )


test_plan_generator = TestPlanGenerator(
    token=token,
    model_id=model_id,
)

bug_report_generator = BugReportGenerator(
    token=token,
    model_id=model_id,
)

orchestrator = TestOrchestrator(
    test_plan_generator=test_plan_generator,
    bug_report_generator=bug_report_generator,
)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )

    try:
        workflow_result = orchestrator.run(
            browser=browser,
            page_url=page_url,
            objective=objective,
        )

    finally:
        browser.close()


print("\nWorkflow completed.")
print(
    f"Test cases executed: "
    f"{len(workflow_result.runs)}"
)

for run in workflow_result.runs:
    print(
        f"- {run.test_result.test_name}: "
        f"{run.test_result.status}"
    )
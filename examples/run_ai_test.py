import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from app.ai.test_plan_generator import TestPlanGenerator
from app.browser.page_inspector import PageInspector
from app.browser.test_case_runner import TestCaseRunner


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)

page_url = html_file.as_uri()

token = os.getenv("HF_TOKEN")
model_id = os.getenv("HF_MODEL")

if not token or not model_id:
    raise RuntimeError(
        "HF_TOKEN or HF_MODEL is missing from .env"
    )


generator = TestPlanGenerator(
    token=token,
    model_id=model_id,
)

inspector = PageInspector()
runner = TestCaseRunner()


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )

    # First browser page: inspect the website.
    inspection_context = browser.new_context()
    inspection_page = inspection_context.new_page()

    inspection_page.goto(
        page_url,
        wait_until="domcontentloaded",
    )

    inspection = inspector.inspect(
        inspection_page
    )

    print("\nDiscovered page elements:")
    print(inspection.model_dump_json(indent=2))

    inspection_context.close()

    # Send discovered elements to Hugging Face.
    test_plan = generator.generate(
        website_name=inspection.title,
        start_url=inspection.url,
        objective=(
            "Test the login form and verify "
            "that signing in displays the welcome message."
        ),
        page_description=inspection.model_dump_json(
            indent=2
        ),
    )

    print("\nGenerated test plan:")
    print(test_plan.model_dump_json(indent=2))

    # Execute every AI-generated test case.
    for test_case in test_plan.test_cases:
        print(f"\nRunning: {test_case.name}")

        result = runner.run(
            browser=browser,
            test_case=test_case,
        )

        print(result.model_dump_json(indent=2))

    browser.close()
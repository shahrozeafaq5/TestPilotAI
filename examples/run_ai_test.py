import os
from pathlib import Path


from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from app.ai.test_plan_generator import TestPlanGenerator
from app.browser.test_case_runner import TestCaseRunner


load_dotenv()

token = os.getenv("HF_TOKEN")
model_id = os.getenv("HF_MODEL")

if not token or not model_id:
    raise RuntimeError(
        "HF_TOKEN or HF_MODEL is missing from .env"
    )


# Locate our sample website.

PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)

if not html_file.exists():
    raise FileNotFoundError(
        f"Sample website not found: {html_file}"
    )

page_url = html_file.as_uri()


# Step 1: Ask Hugging Face to create test cases.
generator = TestPlanGenerator(
    token=token,
    model_id=model_id,
)

test_plan = generator.generate(
    website_name="TestPilot Login",
    start_url=page_url,
    objective=(
        "Fill the login form, click Sign in, "
        "and verify that the welcome message appears."
    ),
    page_description="""
- Heading: TestPilot Login
- Email input with label: Email
- Password input with placeholder: Enter password
- Button with role button and accessible name: Sign in
- Success message text: Welcome to TestPilot!
""",
)

print("\nGenerated test plan:")
print(test_plan.model_dump_json(indent=2))


# Step 2: Execute the generated test cases.
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=False
    )

    runner = TestCaseRunner()

    for test_case in test_plan.test_cases:
        print(f"\nRunning test: {test_case.name}")

        result = runner.run(
            browser=browser,
            test_case=test_case,
        )

        print(result.model_dump_json(indent=2))

    browser.close()
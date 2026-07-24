import os
from pathlib import Path

from dotenv import load_dotenv

from app.ai.test_plan_generator import TestPlanGenerator


load_dotenv()

token = os.getenv("HF_TOKEN")
model_id = os.getenv("HF_MODEL")

if not token or not model_id:
    raise RuntimeError(
        "HF_TOKEN or HF_MODEL is missing from .env"
    )


html_file = PROJECT_ROOT / "samples" / "locator_demo.html"
generator = TestPlanGenerator(
    token=token,
    model_id=model_id,
)

test_plan = generator.generate(
    website_name="TestPilot Login",
    start_url=html_file.as_uri(),
    objective=(
        "Fill the login form, sign in, and verify "
        "that the welcome message appears."
    ),
    page_description="""
- Heading: TestPilot Login
- Email input with label: Email
- Password input with placeholder: Enter password
- Button with role button and name: Sign in
- Successful message text: Welcome to TestPilot!
""",
)

print(test_plan.model_dump_json(indent=2))
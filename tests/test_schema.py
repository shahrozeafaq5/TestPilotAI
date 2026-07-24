import json

from app.models.test_case import TestPlan


sample_data = {
    "website_name": "Example Website",
    "test_cases": [
        {
            "name": "Homepage content test",
            "objective": "Verify that the homepage displays its heading.",
            "start_url": "https://example.com",
            "steps": [
                {
                    "step_number": 1,
                    "description": "Check the main heading",
                    "action": "assert_text",
                    "locator_type": "role",
                    "locator_value": "heading",
                    "expected_text": "Example Domain",
                },
                {
                    "step_number": 2,
                    "description": "Capture final screenshot",
                    "action": "screenshot",
                },
            ],
        }
    ],
}


test_plan = TestPlan.model_validate(sample_data)

print("Validated test plan:\n")
print(test_plan.model_dump_json(indent=2))

print("\nJSON schema for the AI:\n")
print(json.dumps(TestPlan.model_json_schema(), indent=2))
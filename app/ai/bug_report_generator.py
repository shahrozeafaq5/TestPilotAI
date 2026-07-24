import json
import re

from huggingface_hub import InferenceClient

from app.browser.test_case_runner import TestCaseResult
from app.models.bug_report import BugReport


class BugReportGenerator:
    def __init__(
        self,
        token: str,
        model_id: str,
    ) -> None:
        self.model_id = model_id

        self.client = InferenceClient(
            token=token,
            provider="auto",
            timeout=60,
        )

    def has_reportable_issue(
        self,
        result: TestCaseResult,
    ) -> bool:
        diagnostics = result.diagnostics

        return any(
            [
                result.status == "failed",
                bool(diagnostics.console_errors),
                bool(diagnostics.page_errors),
                bool(diagnostics.failed_requests),
                bool(diagnostics.http_errors),
            ]
        )

    def generate(
        self,
        result: TestCaseResult,
    ) -> BugReport | None:
        if not self.has_reportable_issue(result):
            print(
                "No failures or diagnostics were found. "
                "Bug report skipped."
            )
            return None

        prompt = self._build_prompt(result)

        print(
            f"Generating bug report with: "
            f"{self.model_id}"
        )

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior software QA engineer. "
                        "Generate accurate structured bug reports "
                        "using only the provided test evidence. "
                        "Do not invent missing information."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
            max_tokens=1400,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned an empty bug report."
            )

        json_content = self._extract_json(content)

        print("Validating generated bug report...")

        bug_report = BugReport.model_validate_json(
            json_content
        )

        print("Bug report validated successfully.")

        return bug_report

    def _build_prompt(
        self,
        result: TestCaseResult,
    ) -> str:
        schema = BugReport.model_json_schema()

        return f"""
Generate a bug report from the following automated
test result.

Test result:

{result.model_dump_json(indent=2)}

Return exactly one valid JSON object matching this
JSON schema:

{json.dumps(schema, indent=2)}

Severity guidance:

- critical: security issue, data loss, or total system outage
- high: core user flow is completely blocked
- medium: important issue with a possible workaround
- low: minor visual, logging, or non-blocking problem

Rules:

1. Return JSON only.
2. Do not use Markdown code fences.
3. Use only evidence contained in the test result.
4. Do not claim the test failed when its status is passed.
5. Browser diagnostics may still represent a bug even
   when test steps passed.
6. Put console errors, page errors, failed requests,
   HTTP errors, and screenshot paths inside evidence.
7. When the cause is uncertain, clearly state that it
   is a possible cause.
8. Keep reproduction steps clear and sequential.
"""

    def _extract_json(
        self,
        content: str,
    ) -> str:
        cleaned_content = content.strip()

        fenced_match = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```",
            cleaned_content,
            flags=re.DOTALL,
        )

        if fenced_match:
            return fenced_match.group(1)

        start_index = cleaned_content.find("{")
        end_index = cleaned_content.rfind("}")

        if start_index == -1 or end_index == -1:
            raise ValueError(
                "No JSON object was found in the "
                "model response."
            )

        return cleaned_content[
            start_index : end_index + 1
        ]
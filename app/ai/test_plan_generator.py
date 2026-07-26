import json

from huggingface_hub import (
    InferenceClient,
    InferenceTimeoutError,
)
from huggingface_hub.errors import BadRequestError
from pydantic import ValidationError

from app.models.test_case import TestPlan


class TestPlanGenerator:
    def __init__(
        self,
        token: str,
        model_id: str,
        provider: str = "auto",
    ) -> None:
        if not token:
            raise ValueError("HF token is required.")

        if not model_id:
            raise ValueError("HF model ID is required.")

        self.model_id = model_id

        self.client = InferenceClient(
            api_key=token,
            provider=provider,
            timeout=180,
        )

    def generate(
        self,
        website_name: str,
        start_url: str,
        objective: str,
        page_description: str,
    ) -> TestPlan:
        schema = TestPlan.model_json_schema()

        system_prompt = (
            "You generate browser test plans for Playwright. "
            "Use only these actions: click, fill, assert_text, screenshot. "
            "Use only these locator types: role, label, placeholder, text, css. "
            "Number steps starting from 1. "
            "Return only valid JSON with no markdown or explanation."
        )

        user_prompt = (
            f"Website: {website_name}\n"
            f"Start URL: {start_url}\n"
            f"Testing objective: {objective}\n\n"
            f"Visible page elements:\n{page_description}"
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        print(
            f"Sending request to model: {self.model_id}",
            flush=True,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "TestPlan",
                        "schema": schema,
                        "strict": True,
                    },
                },
                temperature=0.1,
                max_tokens=1800,
            )

            print(
                "Structured model response received.",
                flush=True,
            )

        except BadRequestError:
            print(
                "Structured output is unsupported. "
                "Trying normal JSON fallback.",
                flush=True,
            )

            fallback_messages = [
                {
                    "role": "system",
                    "content": (
                        f"{system_prompt}\n\n"
                        "Your response must follow this JSON Schema:\n"
                        f"{json.dumps(schema, indent=2)}"
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]

            try:
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=fallback_messages,
                    temperature=0.1,
                    max_tokens=1800,
                )

                print(
                    "Fallback model response received.",
                    flush=True,
                )

            except InferenceTimeoutError as error:
                raise RuntimeError(
                    "The fallback request timed out after 60 seconds."
                ) from error

            except Exception as error:
                raise RuntimeError(
                    f"Fallback Hugging Face request failed: {error}"
                ) from error

        except InferenceTimeoutError as error:
            raise RuntimeError(
                "Hugging Face did not respond within 60 seconds."
            ) from error

        except Exception as error:
            raise RuntimeError(
                f"Hugging Face request failed: {error}"
            ) from error

        if not response.choices:
            raise RuntimeError(
                "The model returned no response choices."
            )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "The model returned an empty test plan."
            )

        print(
            "Validating generated test plan...",
            flush=True,
        )

        cleaned_content = self._extract_json(content)

        try:
            test_plan = TestPlan.model_validate_json(
                cleaned_content
            )

            print(
                "Test plan validated successfully.",
                flush=True,
            )

            return test_plan

        except ValidationError as error:
            print("\nRaw model response:")
            print(content)

            raise RuntimeError(
                f"Generated test plan failed validation:\n{error}"
            ) from error

    @staticmethod
    def _extract_json(content: str) -> str:
        """
        Remove markdown fences and text surrounding the JSON object.
        """

        cleaned = content.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            # Remove opening ``` or ```json.
            lines = lines[1:]

            # Remove closing ```.
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start == -1 or end == -1 or end < start:
            raise RuntimeError(
                "The model response did not contain a valid JSON object."
            )

        return cleaned[start : end + 1]
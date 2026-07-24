from pathlib import Path

from pydantic import BaseModel
from playwright.sync_api import Page, expect

from app.browser.locator_resolver import resolve_locator
from app.models.test_case import TestStep


class StepResult(BaseModel):
    step_number: int
    description: str
    status: str
    error: str | None = None
    screenshot: str | None = None


class StepExecutor:
    def __init__(
        self,
        screenshots_directory: str = "artifacts",
    ) -> None:
        self.screenshots_directory = Path(
            screenshots_directory
        )

        self.screenshots_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def execute(
        self,
        page: Page,
        step: TestStep,
    ) -> StepResult:
        try:
            if step.action == "screenshot":
                return self._take_screenshot(page, step)

            if not step.locator_type or not step.locator_value:
                raise ValueError(
                    f"Action '{step.action}' requires a locator."
                )

            locator = resolve_locator(
                page=page,
                locator_type=step.locator_type,
                locator_value=step.locator_value,
                locator_name=step.locator_name,
            )

            if step.action == "click":
                locator.click()

            elif step.action == "fill":
                if step.input_value is None:
                    raise ValueError(
                        "Fill action requires input_value."
                    )

                locator.fill(step.input_value)

            elif step.action == "assert_text":
                if step.expected_text is None:
                    raise ValueError(
                        "assert_text requires expected_text."
                    )

                expect(locator).to_contain_text(
                    step.expected_text
                )

            else:
                raise ValueError(
                    f"Unsupported action: {step.action}"
                )

            return StepResult(
                step_number=step.step_number,
                description=step.description,
                status="passed",
            )

        except Exception as error:
            return StepResult(
                step_number=step.step_number,
                description=step.description,
                status="failed",
                error=str(error),
            )

    def _take_screenshot(
        self,
        page: Page,
        step: TestStep,
    ) -> StepResult:
        screenshot_path = (
            self.screenshots_directory
            / f"step_{step.step_number}.png"
        )

        page.screenshot(
            path=str(screenshot_path),
            full_page=True,
        )

        return StepResult(
            step_number=step.step_number,
            description=step.description,
            status="passed",
            screenshot=str(screenshot_path),
        )
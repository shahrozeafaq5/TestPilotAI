from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field
from playwright.sync_api import Browser

from app.browser.step_executor import StepExecutor, StepResult
from app.models.test_case import TestCase


class TestCaseResult(BaseModel):
    run_id: str
    test_name: str
    objective: str
    status: str
    steps: list[StepResult] = Field(default_factory=list)
    error: str | None = None


class TestCaseRunner:
    def __init__(
        self,
        artifacts_directory: str = "artifacts/runs",
    ) -> None:
        self.artifacts_directory = Path(artifacts_directory)
        self.artifacts_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def run(
        self,
        browser: Browser,
        test_case: TestCase,
    ) -> TestCaseResult:
        run_id = uuid4().hex[:8]

        run_directory = (
            self.artifacts_directory / run_id
        )

        run_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = TestCaseResult(
            run_id=run_id,
            test_name=test_case.name,
            objective=test_case.objective,
            status="running",
        )

        # Fresh browser session for this test.
        context = browser.new_context()
        page = context.new_page()

        executor = StepExecutor(
            screenshots_directory=str(run_directory)
        )

        try:
            page.goto(
                test_case.start_url,
                wait_until="domcontentloaded",
                timeout=30_000,
            )

            for step in test_case.steps:
                step_result = executor.execute(
                    page=page,
                    step=step,
                )

                result.steps.append(step_result)

                if step_result.status == "failed":
                    failure_path = (
                        run_directory
                        / f"failure_step_{step.step_number}.png"
                    )

                    page.screenshot(
                        path=str(failure_path),
                        full_page=True,
                    )

                    step_result.screenshot = str(failure_path)
                    result.status = "failed"

                    break

            else:
                # Runs only when the loop finishes without break.
                result.status = "passed"

        except Exception as error:
            result.status = "failed"
            result.error = str(error)

        finally:
            context.close()

        return result
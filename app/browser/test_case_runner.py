from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field
from playwright.sync_api import Browser, Page, Request, Response

from app.browser.step_executor import StepExecutor, StepResult
from app.models.test_case import TestCase


class RunDiagnostics(BaseModel):
    console_errors: list[str] = Field(default_factory=list)
    page_errors: list[str] = Field(default_factory=list)
    failed_requests: list[dict[str, str]] = Field(
        default_factory=list
    )
    http_errors: list[dict[str, str | int]] = Field(
        default_factory=list
    )


class TestCaseResult(BaseModel):
    run_id: str
    test_name: str
    objective: str
    status: str
    steps: list[StepResult] = Field(default_factory=list)
    diagnostics: RunDiagnostics = Field(
        default_factory=RunDiagnostics
    )
    error: str | None = None


class TestCaseRunner:
    def __init__(
        self,
        artifacts_directory: str = "artifacts/runs",
    ) -> None:
        self.artifacts_directory = Path(
            artifacts_directory
        )

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

        diagnostics = RunDiagnostics()

        result = TestCaseResult(
            run_id=run_id,
            test_name=test_case.name,
            objective=test_case.objective,
            status="running",
            diagnostics=diagnostics,
        )

        context = browser.new_context()
        page = context.new_page()

        self._attach_diagnostic_listeners(
            page=page,
            diagnostics=diagnostics,
        )

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

                    step_result.screenshot = str(
                        failure_path
                    )

                    result.status = "failed"
                    break

            else:
                result.status = "passed"

        except Exception as error:
            result.status = "failed"
            result.error = str(error)

            failure_path = (
                run_directory / "unexpected_failure.png"
            )

            try:
                page.screenshot(
                    path=str(failure_path),
                    full_page=True,
                )
            except Exception:
                pass

        finally:
            result.diagnostics = diagnostics
            context.close()

        return result

    def _attach_diagnostic_listeners(
        self,
        page: Page,
        diagnostics: RunDiagnostics,
    ) -> None:
        def handle_console(message) -> None:
            if message.type == "error":
                diagnostics.console_errors.append(
                    message.text
                )

        def handle_page_error(error) -> None:
            diagnostics.page_errors.append(
                str(error)
            )

        def handle_failed_request(
            request: Request,
        ) -> None:
            diagnostics.failed_requests.append(
                {
                    "url": request.url,
                    "error": str(
                        request.failure
                        or "Unknown network failure"
                    ),
                }
            )

        def handle_response(
            response: Response,
        ) -> None:
            if response.status >= 400:
                diagnostics.http_errors.append(
                    {
                        "url": response.url,
                        "status": response.status,
                    }
                )

        page.on("console", handle_console)
        page.on("pageerror", handle_page_error)
        page.on(
            "requestfailed",
            handle_failed_request,
        )
        page.on("response", handle_response)
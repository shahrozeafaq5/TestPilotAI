from pydantic import BaseModel, Field
from playwright.sync_api import Browser

from app.ai.bug_report_generator import (
    BugReportGenerator,
)
from app.ai.test_plan_generator import (
    TestPlanGenerator,
)
from app.browser.page_inspector import (
    PageInspector,
)
from app.browser.test_case_runner import (
    TestCaseResult,
    TestCaseRunner,
)
from app.models.bug_report import BugReport
from app.models.page_inspection import PageInspection
from app.models.test_case import TestPlan
from app.reporting.result_writer import ResultWriter


class WorkflowRunResult(BaseModel):
    test_result: TestCaseResult
    result_path: str

    bug_report: BugReport | None = None
    bug_report_path: str | None = None


class WorkflowResult(BaseModel):
    inspection: PageInspection
    test_plan: TestPlan

    runs: list[WorkflowRunResult] = Field(
        default_factory=list
    )


class TestOrchestrator:
    def __init__(
        self,
        test_plan_generator: TestPlanGenerator,
        bug_report_generator: BugReportGenerator,
        page_inspector: PageInspector | None = None,
        test_case_runner: TestCaseRunner | None = None,
        result_writer: ResultWriter | None = None,
    ) -> None:
        self.test_plan_generator = (
            test_plan_generator
        )

        self.bug_report_generator = (
            bug_report_generator
        )

        self.page_inspector = (
            page_inspector or PageInspector()
        )

        self.test_case_runner = (
            test_case_runner or TestCaseRunner()
        )

        self.result_writer = (
            result_writer or ResultWriter()
        )

    def run(
        self,
        browser: Browser,
        page_url: str,
        objective: str,
    ) -> WorkflowResult:
        inspection = self._inspect_page(
            browser=browser,
            page_url=page_url,
        )

        print("\nDiscovered page elements:")
        print(
            inspection.model_dump_json(indent=2)
        )

        test_plan = (
            self.test_plan_generator.generate(
                website_name=inspection.title,
                start_url=inspection.url,
                objective=objective,
                page_description=(
                    inspection.model_dump_json(
                        indent=2
                    )
                ),
            )
        )

        print("\nGenerated test plan:")
        print(
            test_plan.model_dump_json(indent=2)
        )

        workflow_result = WorkflowResult(
            inspection=inspection,
            test_plan=test_plan,
        )

        for test_case in test_plan.test_cases:
            print(f"\nRunning: {test_case.name}")

            test_result = self.test_case_runner.run(
                browser=browser,
                test_case=test_case,
            )

            result_path = (
                self.result_writer.write_result(
                    test_result
                )
            )

            print("\nTest result:")
            print(
                test_result.model_dump_json(
                    indent=2
                )
            )

            print(
                f"\nResult saved to: {result_path}"
            )

            bug_report = (
                self.bug_report_generator.generate(
                    test_result
                )
            )

            bug_report_path = None

            if bug_report is not None:
                saved_bug_report_path = (
                    self.result_writer
                    .write_bug_report(
                        run_id=test_result.run_id,
                        bug_report=bug_report,
                    )
                )

                bug_report_path = str(
                    saved_bug_report_path
                )

                print("\nGenerated bug report:")
                print(
                    bug_report.model_dump_json(
                        indent=2
                    )
                )

                print(
                    "\nBug report saved to: "
                    f"{saved_bug_report_path}"
                )

            workflow_result.runs.append(
                WorkflowRunResult(
                    test_result=test_result,
                    result_path=str(result_path),
                    bug_report=bug_report,
                    bug_report_path=(
                        bug_report_path
                    ),
                )
            )

        return workflow_result

    def _inspect_page(
        self,
        browser: Browser,
        page_url: str,
    ) -> PageInspection:
        context = browser.new_context()

        try:
            page = context.new_page()

            page.goto(
                page_url,
                wait_until="domcontentloaded",
                timeout=30_000,
            )

            return self.page_inspector.inspect(
                page
            )

        finally:
            context.close()
from datetime import datetime, timezone

from app.browser.step_executor import (
    StepResult as BrowserStepResult,
)
from app.browser.test_case_runner import (
    RunDiagnostics,
    TestCaseResult as BrowserTestCaseResult,
)
from app.models.bug_report import BugReport
from app.models.job import (
    JobStatus,
    TestJob,
)
from app.models.page_inspection import PageInspection
from app.models.test_case import (
    TestCase as GeneratedTestCase,
    TestPlan as GeneratedTestPlan,
    TestStep as GeneratedTestStep,
)
from app.models.run_record import StoredTestRun
from app.services.job_store import JobStore
from app.services.run_store import RunStore
from app.services.test_orchestrator import (
    WorkflowResult,
    WorkflowRunResult,
)


def test_workflow_results_are_stored_in_tables(
    tmp_path,
):
    database_path = tmp_path / "testpilot.db"

    job_store = JobStore(
        database_path=str(database_path)
    )

    run_store = RunStore(
        database_path=str(database_path)
    )

    now = datetime.now(timezone.utc)

    job = StoredJob(
        job_id="job123",
        status="completed",
        page_url="https://example.com",
        objective="Test the login page",
        headless=True,
        created_at=now,
        updated_at=now,
    )

    job_store.create(job)

    test_result = BrowserTestCaseResult(
        run_id="run123",
        test_name="Login test",
        objective="Verify login functionality",
        status="failed",
        steps=[
            BrowserStepResult(
                step_number=1,
                description="Click login button",
                status="failed",
                error="Button was not found",
                screenshot=(
                    "artifacts/runs/run123/"
                    "failure_step_1.png"
                ),
            )
        ],
        diagnostics=RunDiagnostics(
            console_errors=[
                "Example console error"
            ],
            page_errors=[
                "Example JavaScript error"
            ],
            failed_requests=[],
            http_errors=[
                {
                    "url": (
                        "https://example.com/api"
                    ),
                    "status": 500,
                }
            ],
        ),
        error=None,
    )

    bug_report = BugReport(
        title="Login button cannot be found",
        test_name="Login test",
        severity="high",
        summary=(
            "The login flow cannot continue because "
            "the login button was not found."
        ),
        reproduction_steps=[
            "Open the login page.",
            "Attempt to click the login button.",
        ],
        expected_behavior=(
            "The login button should be available."
        ),
        actual_behavior=(
            "The test could not locate the button."
        ),
        evidence=[
            "Button was not found",
            (
                "artifacts/runs/run123/"
                "failure_step_1.png"
            ),
        ],
        likely_cause=(
            "The button locator may have changed."
        ),
        recommended_fix=(
            "Review the login button markup and "
            "update its accessible name."
        ),
    )

    workflow_result = WorkflowResult(
        inspection=PageInspection(
            title="Example Login",
            url="https://example.com",
            elements=[],
        ),
test_plan=GeneratedTestPlan(
    website_name="Example",
    test_cases=[
        GeneratedTestCase(
            name="Login test",
            objective="Verify login functionality",
            start_url="https://example.com",
            steps=[
                GeneratedTestStep(
                    step_number=1,
                    description="Click login button",
                    action="click",
                    locator_type="text",
                    locator_value="Login",
                )
            ],
        )
    ],
),
runs=[
            WorkflowRunResult(
                test_result=test_result,
                bug_report=bug_report,
            )
        ],
    )
    run_store.save_workflow(
        job_id="job123",
        workflow_result=workflow_result,
    )

    saved_runs = run_store.list_by_job_id(
        "job123"
    )

    assert len(saved_runs) == 1

    saved_run = saved_runs[0]

    assert saved_run.run_id == "run123"
    assert saved_run.job_id == "job123"
    assert saved_run.status == "failed"

    assert len(saved_run.steps) == 1
    assert saved_run.steps[0].step_number == 1
    assert saved_run.steps[0].status == "failed"

    assert saved_run.diagnostics.console_errors == [
        "Example console error"
    ]

    assert saved_run.diagnostics.http_errors == [
        {
            "url": "https://example.com/api",
            "status": 500,
        }
    ]

    assert saved_run.bug_report is not None
    assert saved_run.bug_report.severity == "high"
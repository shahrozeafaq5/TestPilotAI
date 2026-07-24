import json

from app.browser.step_executor import (
    StepResult as BrowserStepResult,
)
from app.browser.test_case_runner import (
    RunDiagnostics,
    TestCaseResult as BrowserTestCaseResult,
)
from app.reporting.result_writer import ResultWriter


def test_result_writer_creates_json_report(
    tmp_path,
):
    result = BrowserTestCaseResult(
        run_id="demo1234",
        test_name="Example login test",
        objective="Verify login functionality.",
        status="failed",
        steps=[
            BrowserStepResult(
                step_number=1,
                description="Click login button",
                status="failed",
                error="Button was not found",
                screenshot=(
                    "artifacts/runs/demo1234/"
                    "failure_step_1.png"
                ),
            )
        ],
        diagnostics=RunDiagnostics(
            console_errors=[
                "Uncaught JavaScript error"
            ],
            page_errors=[],
            failed_requests=[],
            http_errors=[],
        ),
        error=None,
    )

    writer = ResultWriter(
        reports_directory=str(tmp_path)
    )

    report_path = writer.write(result)

    assert report_path.exists()
    assert report_path.name == "result.json"

    saved_data = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    assert saved_data["run_id"] == "demo1234"
    assert saved_data["status"] == "failed"
    assert len(saved_data["steps"]) == 1

    assert saved_data["diagnostics"][
        "console_errors"
    ] == [
        "Uncaught JavaScript error"
    ]
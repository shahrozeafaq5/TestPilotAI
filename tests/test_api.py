import time
from pathlib import Path

import pytest
from fastapi.testclient import (
    TestClient as FastAPITestClient,
)

import app.main as main_module
from app.browser.step_executor import (
    StepResult as BrowserStepResult,
)
from app.browser.test_case_runner import (
    RunDiagnostics,
    TestCaseResult as BrowserTestCaseResult,
)
from app.models.page_inspection import PageInspection
from app.models.test_case import (
    TestCase as GeneratedTestCase,
    TestPlan as GeneratedTestPlan,
    TestStep as GeneratedTestStep,
)
from app.services.test_orchestrator import (
    WorkflowResult,
    WorkflowRunResult,
)


class FakeOrchestrator:
    """
    Replaces Hugging Face and real AI planning during
    API tests.

    It returns a predictable completed workflow.
    """

    def __init__(
        self,
        artifacts_directory: Path,
    ) -> None:
        self.artifacts_directory = artifacts_directory

    def run(
        self,
        browser,
        page_url: str,
        objective: str,
    ) -> WorkflowResult:
        run_id = "fake-api-run"

        run_directory = (
            self.artifacts_directory / run_id
        )

        run_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        screenshot_path = (
            run_directory / "step_1.png"
        )

        screenshot_path.write_bytes(
            b"fake screenshot content"
        )

        inspection = PageInspection(
            title="Fake Login Page",
            url=page_url,
            elements=[],
        )

        test_plan = GeneratedTestPlan(
            website_name="Fake Login Page",
            test_cases=[
                GeneratedTestCase(
                    name="Fake login test",
                    objective=objective,
                    start_url=page_url,
                    steps=[
                        GeneratedTestStep(
                            step_number=1,
                            description=(
                                "Capture login page"
                            ),
                            action="screenshot",
                        )
                    ],
                )
            ],
        )

        test_result = BrowserTestCaseResult(
            run_id=run_id,
            test_name="Fake login test",
            objective=objective,
            status="passed",
            steps=[
                BrowserStepResult(
                    step_number=1,
                    description="Capture login page",
                    status="passed",
                    error=None,
                    screenshot=str(
                        screenshot_path.resolve()
                    ),
                )
            ],
            diagnostics=RunDiagnostics(),
            error=None,
        )

        return WorkflowResult(
            inspection=inspection,
            test_plan=test_plan,
            runs=[
                WorkflowRunResult(
                    test_result=test_result,
                    bug_report=None,
                )
            ],
        )


@pytest.fixture
def api_client(
    tmp_path,
    monkeypatch,
):
    database_path = (
        tmp_path / "testpilot.db"
    )

    artifacts_path = (
        tmp_path / "artifacts" / "runs"
    )

    monkeypatch.setenv(
        "TESTPILOT_DB_PATH",
        str(database_path),
    )

    monkeypatch.setenv(
        "TESTPILOT_ARTIFACTS_PATH",
        str(artifacts_path),
    )

    fake_orchestrator = FakeOrchestrator(
        artifacts_directory=artifacts_path
    )

    monkeypatch.setattr(
        main_module,
        "create_orchestrator",
        lambda: fake_orchestrator,
    )

    with FastAPITestClient(
        main_module.app
    ) as client:
        yield client


def wait_for_job(
    client: FastAPITestClient,
    job_id: str,
    timeout_seconds: float = 10,
) -> dict:
    deadline = (
        time.monotonic() + timeout_seconds
    )

    while time.monotonic() < deadline:
        response = client.get(
            f"/tests/jobs/{job_id}"
        )

        assert response.status_code == 200

        job = response.json()

        if job["status"] in {
            "completed",
            "failed",
            "cancelled",
        }:
            return job

        time.sleep(0.1)

    pytest.fail(
        "Background test job did not finish "
        "within the expected time."
    )


def test_health_endpoint(
    api_client: FastAPITestClient,
):
    response = api_client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "service": "TestPilot AI",
    }


def test_complete_api_workflow(
    api_client: FastAPITestClient,
):
    # Submit a background test job.
    submission_response = api_client.post(
        "/tests/run",
        json={
            "page_url": (
                "https://example.com/login"
            ),
            "objective": (
                "Test the login page and capture "
                "a screenshot."
            ),
            "headless": True,
        },
    )

    assert submission_response.status_code == 202

    submission = submission_response.json()

    assert "job_id" in submission
    assert submission["status"] in {
        "queued",
        "running",
    }

    job_id = submission["job_id"]

    # Wait for the worker to complete.
    completed_job = wait_for_job(
        client=api_client,
        job_id=job_id,
    )

    assert completed_job["status"] == "completed"
    assert completed_job["error"] is None

    summary = completed_job["result"]

    assert summary["total_runs"] == 1
    assert summary["passed_runs"] == 1
    assert summary["failed_runs"] == 0
    assert summary["bug_reports"] == 0
    assert summary["run_ids"] == [
        "fake-api-run"
    ]

    # Verify that the job appears in history.
    history_response = api_client.get(
        "/tests/jobs?status=completed&limit=10"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert history["count"] == 1
    assert history["jobs"][0]["job_id"] == job_id

    # Retrieve normalized database runs.
    runs_response = api_client.get(
        f"/tests/jobs/{job_id}/runs"
    )

    assert runs_response.status_code == 200

    runs_data = runs_response.json()

    assert runs_data["count"] == 1

    stored_run = runs_data["runs"][0]

    assert stored_run["run_id"] == "fake-api-run"
    assert stored_run["status"] == "passed"
    assert len(stored_run["steps"]) == 1

    # Retrieve one complete run.
    run_response = api_client.get(
        "/tests/runs/fake-api-run"
    )

    assert run_response.status_code == 200

    run_data = run_response.json()

    assert run_data["test_name"] == (
        "Fake login test"
    )

    assert run_data["steps"][0]["status"] == (
        "passed"
    )

    assert run_data["diagnostics"] == {
        "console_errors": [],
        "page_errors": [],
        "failed_requests": [],
        "http_errors": [],
    }

    # Download the screenshot through the API.
    screenshot_response = api_client.get(
        "/tests/runs/fake-api-run/"
        "screenshots/step_1.png"
    )

    assert screenshot_response.status_code == 200

    assert screenshot_response.content == (
        b"fake screenshot content"
    )

    # Delete the completed job.
    delete_response = api_client.delete(
        f"/tests/jobs/{job_id}"
    )

    assert delete_response.status_code == 200

    assert delete_response.json() == {
        "job_id": job_id,
        "message": "Test job was deleted.",
    }

    # The job and its cascaded runs should be gone.
    missing_job_response = api_client.get(
        f"/tests/jobs/{job_id}"
    )

    assert missing_job_response.status_code == 404

    missing_run_response = api_client.get(
        "/tests/runs/fake-api-run"
    )

    assert missing_run_response.status_code == 404
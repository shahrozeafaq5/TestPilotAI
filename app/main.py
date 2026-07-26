import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import FileResponse

from app.ai.bug_report_generator import BugReportGenerator
from app.ai.test_plan_generator import TestPlanGenerator
from app.api.schemas import (
    HealthResponse,
    JobCreatedResponse,
    JobDeletedResponse,
    JobListResponse,
    JobRunsResponse,
    RunTestRequest,
)
from app.models.job import JobStatus, TestJob
from app.models.run_record import StoredTestRun
from app.services.artifact_service import (
    ArtifactNotFoundError,
    ArtifactService,
    InvalidArtifactNameError,
)
from app.services.job_manager import TestJobManager
from app.services.job_store import JobStore
from app.services.run_store import RunStore
from app.services.test_orchestrator import TestOrchestrator


load_dotenv()


def create_orchestrator() -> TestOrchestrator:
    """Create the shared TestPilot workflow service."""

    token = os.getenv("HF_TOKEN")
    model_id = os.getenv("HF_MODEL")

    if not token:
        raise RuntimeError(
            "HF_TOKEN is missing from .env"
        )

    if not model_id:
        raise RuntimeError(
            "HF_MODEL is missing from .env"
        )

    test_plan_generator = TestPlanGenerator(
        token=token,
        model_id=model_id,
    )

    bug_report_generator = BugReportGenerator(
        token=token,
        model_id=model_id,
    )

    return TestOrchestrator(
        test_plan_generator=test_plan_generator,
        bug_report_generator=bug_report_generator,
    )


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """Create shared services at startup and clean up at shutdown."""

    print("Starting TestPilot API...")

    orchestrator = create_orchestrator()

    database_path = os.getenv(
        "TESTPILOT_DB_PATH",
        "data/testpilot.db",
    )

    artifacts_path = os.getenv(
        "TESTPILOT_ARTIFACTS_PATH",
        "artifacts/runs",
    )

    job_store = JobStore(
        database_path=database_path,
    )

    run_store = RunStore(
        database_path=database_path,
    )

    interrupted_jobs = (
        job_store.mark_incomplete_as_failed()
    )

    if interrupted_jobs:
        print(
            f"Marked {interrupted_jobs} interrupted "
            "job(s) as failed."
        )

    app.state.job_manager = TestJobManager(
        orchestrator=orchestrator,
        job_store=job_store,
        run_store=run_store,
        max_workers=1,
    )

    app.state.artifact_service = ArtifactService(
        runs_directory=artifacts_path,
    )

    try:
        yield

    finally:
        app.state.job_manager.shutdown()
        print("Stopping TestPilot API...")


app = FastAPI(
    title="TestPilot AI API",
    description=(
        "AI-powered autonomous web testing "
        "and bug-reporting API."
    ),
    version="0.5.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """Verify that the API is running."""

    return HealthResponse(
        status="healthy",
        service="TestPilot AI",
    )


@app.post(
    "/tests/run",
    response_model=JobCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_test(
    payload: RunTestRequest,
    request: Request,
) -> JobCreatedResponse:
    """Submit a website test as a background job."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    job = job_manager.submit(
        page_url=payload.page_url,
        objective=payload.objective,
        headless=payload.headless,
    )

    return JobCreatedResponse(
        job_id=job.job_id,
        status=job.status,
        status_url=f"/tests/jobs/{job.job_id}",
    )


@app.get(
    "/tests/jobs",
    response_model=JobListResponse,
)
def list_test_jobs(
    request: Request,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    job_status: JobStatus | None = Query(
        default=None,
        alias="status",
    ),
) -> JobListResponse:
    """Return recent jobs, optionally filtered by status."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    jobs = job_manager.list_recent(
        limit=limit,
        status=job_status,
    )

    return JobListResponse(
        count=len(jobs),
        jobs=jobs,
    )


@app.get(
    "/tests/jobs/{job_id}/runs",
    response_model=JobRunsResponse,
)
def list_job_runs(
    job_id: str,
    request: Request,
) -> JobRunsResponse:
    """Return all detailed runs belonging to one job."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    job = job_manager.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test job was not found.",
        )

    runs = job_manager.list_runs(job_id)

    return JobRunsResponse(
        job_id=job_id,
        count=len(runs),
        runs=runs,
    )


@app.get(
    "/tests/runs/{run_id}",
    response_model=StoredTestRun,
)
def get_test_run(
    run_id: str,
    request: Request,
) -> StoredTestRun:
    """Return one run with steps, diagnostics, and bug report."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    run = job_manager.get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run was not found.",
        )

    return run


@app.get(
    "/tests/runs/{run_id}/screenshots/{filename}",
    response_class=FileResponse,
)
def get_run_screenshot(
    run_id: str,
    filename: str,
    request: Request,
) -> FileResponse:
    """Return a screenshot associated with a stored test run."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    artifact_service: ArtifactService = (
        request.app.state.artifact_service
    )

    run = job_manager.get_run(run_id)

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test run was not found.",
        )

    try:
        screenshot_path = artifact_service.get_screenshot(
            run=run,
            filename=filename,
        )

    except InvalidArtifactNameError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except ArtifactNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return FileResponse(
        path=screenshot_path,
        filename=filename,
    )


@app.post(
    "/tests/jobs/{job_id}/cancel",
    response_model=TestJob,
)
def cancel_test_job(
    job_id: str,
    request: Request,
) -> TestJob:
    """Cancel a job that is still queued."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    try:
        job = job_manager.cancel(job_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test job was not found.",
        )

    return job


@app.delete(
    "/tests/jobs/{job_id}",
    response_model=JobDeletedResponse,
)
def delete_test_job(
    job_id: str,
    request: Request,
) -> JobDeletedResponse:
    """Delete a completed, failed, or cancelled job."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    try:
        deleted = job_manager.delete(job_id)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test job was not found.",
        )

    return JobDeletedResponse(
        job_id=job_id,
        message="Test job was deleted.",
    )


@app.get(
    "/tests/jobs/{job_id}",
    response_model=TestJob,
)
def get_test_job(
    job_id: str,
    request: Request,
) -> TestJob:
    """Return one job's status and summary."""

    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    job = job_manager.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test job was not found.",
        )

    return job
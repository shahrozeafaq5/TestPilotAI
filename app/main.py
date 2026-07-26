import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    status,
)

from app.ai.bug_report_generator import (
    BugReportGenerator,
)
from app.ai.test_plan_generator import (
    TestPlanGenerator,
)
from app.api.schemas import (
    HealthResponse,
    JobCreatedResponse,
    RunTestRequest,
)
from app.services.job_manager import (
    TestJob,
    TestJobManager,
)
from app.services.test_orchestrator import (
    TestOrchestrator,
)


load_dotenv()


def create_orchestrator() -> TestOrchestrator:
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
    print("Starting TestPilot API...")

    orchestrator = create_orchestrator()

    app.state.job_manager = TestJobManager(
        orchestrator=orchestrator,
        max_workers=1,
    )

    yield

    app.state.job_manager.shutdown()

    print("Stopping TestPilot API...")


app = FastAPI(
    title="TestPilot AI API",
    description=(
        "AI-powered autonomous web testing "
        "and bug-reporting API."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
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
        status_url=(
            f"/tests/jobs/{job.job_id}"
        ),
    )


@app.get(
    "/tests/jobs/{job_id}",
    response_model=TestJob,
)
def get_test_job(
    job_id: str,
    request: Request,
) -> TestJob:
    job_manager: TestJobManager = (
        request.app.state.job_manager
    )

    job = job_manager.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Test job was not found.",
        )

    return job
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)
from playwright.sync_api import sync_playwright

from app.ai.bug_report_generator import (
    BugReportGenerator,
)
from app.ai.test_plan_generator import (
    TestPlanGenerator,
)
from app.api.schemas import (
    HealthResponse,
    RunTestRequest,
)
from app.services.test_orchestrator import (
    TestOrchestrator,
    WorkflowResult,
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

    app.state.orchestrator = (
        create_orchestrator()
    )

    yield

    print("Stopping TestPilot API...")


app = FastAPI(
    title="TestPilot AI API",
    description=(
        "AI-powered autonomous web testing "
        "and bug-reporting API."
    ),
    version="0.1.0",
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
    response_model=WorkflowResult,
)
def run_test(
    payload: RunTestRequest,
    request: Request,
) -> WorkflowResult:
    orchestrator: TestOrchestrator = (
        request.app.state.orchestrator
    )

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=payload.headless
            )

            try:
                workflow_result = orchestrator.run(
                    browser=browser,
                    page_url=payload.page_url,
                    objective=payload.objective,
                )

                return workflow_result

            finally:
                browser.close()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Test execution failed: {error}",
        ) from error
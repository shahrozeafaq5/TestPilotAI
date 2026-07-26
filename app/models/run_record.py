from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.bug_report import BugReport


class StoredTestStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int
    description: str
    status: str
    error: str | None = None
    screenshot: str | None = None


class StoredDiagnostics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    console_errors: list[str] = Field(
        default_factory=list
    )

    page_errors: list[str] = Field(
        default_factory=list
    )

    failed_requests: list[
        dict[str, str]
    ] = Field(
        default_factory=list
    )

    http_errors: list[
        dict[str, Any]
    ] = Field(
        default_factory=list
    )


class StoredTestRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    job_id: str

    test_name: str
    objective: str
    status: str
    error: str | None = None

    created_at: datetime

    steps: list[StoredTestStep] = Field(
        default_factory=list
    )

    diagnostics: StoredDiagnostics = Field(
        default_factory=StoredDiagnostics
    )

    bug_report: BugReport | None = None
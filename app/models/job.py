from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


JobStatus = Literal[
    "queued",
    "running",
    "completed",
    "failed",
]


class TestJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus

    page_url: str
    objective: str
    headless: bool

    created_at: datetime
    updated_at: datetime

    result: dict[str, Any] | None = None
    error: str | None = None
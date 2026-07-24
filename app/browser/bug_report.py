from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SeverityLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class BugReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    test_name: str
    severity: SeverityLevel

    summary: str

    reproduction_steps: list[str] = Field(
        default_factory=list
    )

    expected_behavior: str
    actual_behavior: str

    evidence: list[str] = Field(
        default_factory=list
    )

    likely_cause: str
    recommended_fix: str
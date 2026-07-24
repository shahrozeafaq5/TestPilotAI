from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ActionType = Literal[
    "click",
    "fill",
    "assert_text",
    "screenshot",
]

LocatorType = Literal[
    "role",
    "label",
    "placeholder",
    "text",
    "css",
]


class TestStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locator_name: str | None = None
    step_number: int = Field(ge=1)
    description: str = Field(min_length=3)

    action: ActionType

    locator_type: LocatorType | None = None
    locator_value: str | None = None

    input_value: str | None = None
    expected_text: str | None = None


class TestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3)
    objective: str = Field(min_length=5)
    start_url: str
    steps: list[TestStep] = Field(min_length=1)


class TestPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    website_name: str
    test_cases: list[TestCase] = Field(min_length=1)
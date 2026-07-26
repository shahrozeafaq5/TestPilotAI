from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class RunTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_url: str

    objective: str = Field(
        min_length=5,
        max_length=1000,
    )

    headless: bool = True

    @field_validator("page_url")
    @classmethod
    def validate_page_url(
        cls,
        value: str,
    ) -> str:
        cleaned_value = value.strip()
        parsed_url = urlparse(cleaned_value)

        supported_schemes = {
            "http",
            "https",
            "file",
        }

        if parsed_url.scheme not in supported_schemes:
            raise ValueError(
                "page_url must use http, https, "
                "or file scheme"
            )

        return cleaned_value


class HealthResponse(BaseModel):
    status: str
    service: str
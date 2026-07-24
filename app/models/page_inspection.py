from pydantic import BaseModel, Field


class PageElement(BaseModel):
    tag: str
    element_type: str | None = None
    role: str | None = None
    name: str | None = None
    label: str | None = None
    placeholder: str | None = None
    text: str | None = None
    visible: bool


class PageInspection(BaseModel):
    title: str
    url: str
    elements: list[PageElement] = Field(default_factory=list)
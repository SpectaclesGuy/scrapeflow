from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


FieldType = Literal['text', 'attribute', 'href', 'src', 'html']
ModeType = Literal['auto', 'http', 'browser']
PaginationType = Literal['none', 'next_button', 'url_pattern']
SLMProviderType = Literal['mock', 'external_http', 'openai_compatible', 'ollama_compatible']


class ScrapeField(BaseModel):
    name: str
    selector: str | None = None
    type: FieldType = 'text'
    required: bool = False
    attribute_name: str | None = None


class PaginationConfig(BaseModel):
    enabled: bool = False
    type: PaginationType = 'none'
    next_selector: str | None = None
    url_pattern: str | None = None
    max_pages: int = 1


class BrowserConfig(BaseModel):
    headless: bool = True
    wait_until: str = 'networkidle'
    timeout: int = 30000
    wait_for_selector: str | None = None


class SLMConfig(BaseModel):
    enabled: bool = True
    provider: SLMProviderType = 'mock'
    model: str = 'mock-scrapeflow-slm'
    max_input_chars: int = 12000


class OutputConfig(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ['json', 'csv'])
    include_evidence: bool = True


class ScrapeJobConfig(BaseModel):
    job_id: str | None = None
    project_id: str | None = None
    target_url: str
    mode: ModeType = 'auto'
    entity: str = 'record'
    container_selector: str | None = None
    fields: list[ScrapeField]
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    slm: SLMConfig = Field(default_factory=SLMConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @field_validator('fields')
    @classmethod
    def validate_fields(cls, value: list[ScrapeField]) -> list[ScrapeField]:
        if not value:
            raise ValueError('At least one field is required')
        return value


class ScrapeRunRequest(BaseModel):
    config: ScrapeJobConfig


class ScrapeResultPreview(BaseModel):
    records: list[dict[str, Any]]


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    records: list[dict[str, Any]]
    output_paths: dict[str, str] = Field(default_factory=dict)

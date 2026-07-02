from typing import Any

from pydantic import BaseModel, Field


class FieldEvidence(BaseModel):
    field: str
    selector: str | None = None
    raw_value: str | None = None
    cleaned_value: str | None = None
    source_url: str
    page_number: int
    method: str
    confidence: float | None = None
    reason: str | None = None
    extracted_at: str


class ExtractionRecord(BaseModel):
    data: dict[str, Any]
    evidence: dict[str, FieldEvidence]
    warnings: list[str] = Field(default_factory=list)


class JobRunSummary(BaseModel):
    job_id: str | None = None
    project_id: str | None = None
    status: str
    pages_processed: int
    records_found: int
    output_paths: dict[str, str] = Field(default_factory=dict)
    records: list[ExtractionRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

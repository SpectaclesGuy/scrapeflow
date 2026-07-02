from typing import Any

from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class JobCreate(BaseModel):
    project_id: str
    conversation_id: str | None = None
    status: str = 'created'
    job_type: str = 'extraction'
    config: dict[str, Any] | None = None
    result_location: str | None = None
    error_message: str | None = None
    progress: int = 0
    pages_processed: int = 0
    records_found: int = 0
    output_paths: dict[str, str] | None = None


class JobUpdate(BaseModel):
    status: str | None = None
    job_type: str | None = None
    config: dict[str, Any] | None = None
    result_location: str | None = None
    error_message: str | None = None
    conversation_id: str | None = None
    progress: int | None = None
    pages_processed: int | None = None
    records_found: int | None = None
    output_paths: dict[str, str] | None = None


class JobRead(TimestampedSchema):
    id: str
    project_id: str
    conversation_id: str | None = None
    status: str
    job_type: str
    config: dict[str, Any] | None = None
    result_location: str | None = None
    error_message: str | None = None
    progress: int
    pages_processed: int
    records_found: int
    output_paths: dict[str, str] | None = None

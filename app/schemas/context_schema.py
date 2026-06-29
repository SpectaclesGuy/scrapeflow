from typing import Any

from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class ProjectContextBase(BaseModel):
    target_url: str | None = None
    domain: str | None = None
    entity: str | None = None
    fields: list[str] | None = None
    filters: list[dict[str, Any] | str] | None = None
    pagination: dict[str, Any] | None = None
    auth_required: bool | None = None
    export_format: str | None = None
    schedule: dict[str, Any] | None = None
    current_plan: dict[str, Any] | None = None
    current_schema: dict[str, Any] | None = None
    summary: str | None = None
    status: str | None = None
    version: int | None = None


class ProjectContextUpdate(ProjectContextBase):
    pass


class ProjectContextRead(TimestampedSchema):
    id: str
    project_id: str
    target_url: str | None = None
    domain: str | None = None
    entity: str | None = None
    fields: list[str]
    filters: list[dict[str, Any] | str]
    pagination: dict[str, Any] | None = None
    auth_required: bool
    export_format: str | None = None
    schedule: dict[str, Any] | None = None
    current_plan: dict[str, Any] | None = None
    current_schema: dict[str, Any] | None = None
    summary: str | None = None
    status: str
    version: int

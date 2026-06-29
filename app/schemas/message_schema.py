from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, Field

from app.schemas.common import ORMModel


class MessageCreate(BaseModel):
    role: str
    content: str
    metadata: dict[str, Any] | None = None


class MessageRead(ORMModel):
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: dict[str, Any] | None = Field(
        default=None, validation_alias=AliasChoices("metadata", "meta")
    )
    created_at: datetime

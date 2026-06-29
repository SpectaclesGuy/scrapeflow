from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class ConversationCreate(BaseModel):
    project_id: str
    user_id: str
    title: str | None = None
    status: str = "active"


class ConversationRead(TimestampedSchema):
    id: str
    project_id: str
    user_id: str
    title: str | None = None
    status: str

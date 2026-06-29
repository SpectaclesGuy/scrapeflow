from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class ProjectCreate(BaseModel):
    user_id: str
    name: str
    description: str | None = None
    status: str = "active"


class ProjectRead(TimestampedSchema):
    id: str
    user_id: str
    name: str
    description: str | None = None
    status: str

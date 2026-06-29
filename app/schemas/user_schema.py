from pydantic import BaseModel, EmailStr

from app.schemas.common import TimestampedSchema


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password_hash: str | None = None
    role: str = "user"
    plan: str = "free"


class UserRead(TimestampedSchema):
    id: str
    name: str
    email: EmailStr
    password_hash: str | None = None
    role: str
    plan: str

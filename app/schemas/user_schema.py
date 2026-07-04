from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel, TimestampedSchema


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str | None = None
    password_hash: str | None = None
    role: str = 'user'
    plan: str = 'free'


class UserRead(TimestampedSchema):
    id: str
    name: str
    email: EmailStr
    role: str
    plan: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class SessionRead(ORMModel):
    id: str
    name: str
    email: EmailStr
    role: str
    plan: str

from __future__ import annotations

import secrets

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user_schema import LoginRequest, SessionRead, SignupRequest, UserCreate
from app.services.security_service import hash_password, verify_password


SESSION_USER_KEY = 'user'


def serialize_user(user: User) -> dict:
    return SessionRead.model_validate(user).model_dump()


def create_user_record(db: Session, payload: UserCreate) -> User:
    password_input = payload.password or payload.password_hash
    password_hash = hash_password(password_input) if password_input else None
    user = User(
        name=payload.name,
        email=str(payload.email),
        password_hash=password_hash,
        role=payload.role,
        plan=payload.plan,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already exists') from exc
    db.refresh(user)
    return user


def signup_user(db: Session, payload: SignupRequest) -> User:
    return create_user_record(
        db,
        UserCreate(name=payload.name, email=payload.email, password=payload.password),
    )


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    user = db.query(User).filter(User.email == str(payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')
    return user


def set_user_session(request: Request, user: User) -> dict:
    payload = serialize_user(user)
    request.session.clear()
    request.session[SESSION_USER_KEY] = payload
    request.session['nonce'] = secrets.token_urlsafe(18)
    return payload


def clear_user_session(request: Request) -> None:
    request.session.clear()


def get_session_user(request: Request) -> dict | None:
    return request.session.get(SESSION_USER_KEY)


def require_session_user(request: Request) -> dict:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    return user


def get_or_create_google_user(db: Session, email: str, name: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user
    user = User(name=name, email=email, password_hash=None, role='user', plan='free')
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unable to create Google user') from exc
    db.refresh(user)
    return user

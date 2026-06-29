from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserRead
from app.utils.response import success_response

router = APIRouter(tags=["users"])


@router.post("/users")
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> dict:
    user = User(**payload.model_dump())
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists") from exc
    db.refresh(user)
    return success_response("User created successfully", UserRead.model_validate(user).model_dump())


@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return success_response("User fetched successfully", UserRead.model_validate(user).model_dump())

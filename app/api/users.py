from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.user import UserResponse
from app.services.user_service import UserService


# VS talks about the flow below
# HTTP request
#     ↓
# Route
#     ↓
# Service
#     ↓
# Repository
#     ↓
# SQLAlchemy
#     ↓
# PostgreSQL

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
)
def create_user(
    db: Session = Depends(get_db),
):
    service = UserService(db)

    return service.create_user()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    service = UserService(db)

    user = service.get_user(user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    pass


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None
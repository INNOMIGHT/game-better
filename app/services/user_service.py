from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self) -> User:
        return self.repository.create()

    def get_user(self, user_id: int) -> User | None:
        return self.repository.get_by_id(user_id)
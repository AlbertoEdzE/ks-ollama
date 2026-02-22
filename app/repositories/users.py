from sqlalchemy.orm import Session
from sqlalchemy import select
from app.domain import models

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> models.User | None:
        return self.db.get(models.User, user_id)

    def get_by_email(self, email: str) -> models.User | None:
        return self.db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()

    def create(self, email: str, display_name: str | None) -> models.User:
        user = models.User(email=email, display_name=display_name)
        self.db.add(user)
        self.db.flush()
        return user

    def set_roles(self, user: models.User, roles: list[str]):
        existing = {r.name: r for r in self.db.query(models.Role).all()}
        assigned = []
        for name in roles or []:
            role = existing.get(name)
            if role is None:
                role = models.Role(name=name)
                self.db.add(role)
                self.db.flush()
            assigned.append(role)
        user.roles = assigned
        self.db.flush()

    def update(self, user: models.User, display_name: str | None = None, is_active: bool | None = None):
        if display_name is not None:
            user.display_name = display_name
        if is_active is not None:
            user.is_active = is_active
        self.db.flush()

    def delete(self, user: models.User):
        self.db.delete(user)

import secrets
from typing import Optional
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from app.domain import models

ph = PasswordHasher()


class CredentialService:
    def __init__(self, db: Session):
        self.db = db

    def generate_secret(self) -> str:
        return secrets.token_urlsafe(48)

    def hash_secret(self, secret: str) -> str:
        return ph.hash(secret)

    def create(self, user_id: int, label: Optional[str] = None) -> tuple[int, str]:
        secret = self.generate_secret()
        hashed = self.hash_secret(secret)
        cred = models.Credential(user_id=user_id, hash=hashed, alg="argon2id", label=label)
        self.db.add(cred)
        self.db.flush()
        return cred.id, secret

    def revoke(self, credential_id: int):
        cred = (
            self.db.query(models.Credential)
            .filter(models.Credential.id == credential_id, models.Credential.revoked.is_(False))
            .one_or_none()
        )
        if not cred:
            return False
        cred.revoked = True
        return True

    def set_password(self, user_id: int, password: str):
        existing = (
            self.db.query(models.Credential)
            .filter(models.Credential.user_id == user_id, models.Credential.label == "password", models.Credential.revoked.is_(False))
            .all()
        )
        for cred in existing:
            cred.revoked = True
        hashed = self.hash_secret(password)
        cred = models.Credential(user_id=user_id, hash=hashed, alg="argon2id", label="password")
        self.db.add(cred)
        self.db.flush()
        return cred.id

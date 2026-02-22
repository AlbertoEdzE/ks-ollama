from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from argon2 import PasswordHasher, exceptions as argon_exc
from sqlalchemy.orm import Session
from app.config import settings
from app.domain import models

ph = PasswordHasher()


def create_jwt(subject: str, roles: list[str], expires_minutes: int = 60) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {"sub": subject, "roles": roles, "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=expires_minutes)).timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def verify_jwt(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


def _verify_user_password(db: Session, email: str, password: str) -> Optional[models.User]:
    user = db.query(models.User).filter(models.User.email == email, models.User.is_active).one_or_none()
    if user is None:
        return None
    creds = (
        db.query(models.Credential)
        .filter(models.Credential.user_id == user.id, models.Credential.revoked.is_(False), models.Credential.label == "password")
        .all()
    )
    for cred in creds:
        try:
            if ph.verify(cred.hash, password):
                return user
        except argon_exc.VerifyMismatchError:
            continue
    return None


def authenticate_credentials(db: Session, username: str, password: str) -> Optional[models.User]:
    return _verify_user_password(db, username, password)


def log_auth_event(db: Session, user_id: int | None, credential_id: int | None, event_type: str, ip: str | None, user_agent: str | None, detail: str | None = None) -> None:
    entry = models.AuditLog(user_id=user_id, credential_id=credential_id, event_type=event_type, ip=ip, user_agent=user_agent, detail=detail)
    db.add(entry)

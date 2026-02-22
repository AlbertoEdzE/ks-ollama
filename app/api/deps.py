from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import jwt
from app.db.session import get_db
from app.services.auth import verify_jwt
from app.services.rate_limit import RateLimiter
from app.domain import models

rate_limiter = RateLimiter()


def get_current_principal(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = verify_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.get(models.User, int(subject))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not active")
    return user, None


def enforce_rate_limit(user_id: int):
    allowed, remaining, reset = rate_limiter.allow(f"user:{user_id}")
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return remaining, reset

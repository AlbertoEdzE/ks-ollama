from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth import create_jwt, authenticate_credentials, log_auth_event, verify_jwt
from app.services.rate_limit import RateLimiter
from app.domain.schemas import LoginRequest, LoginResponse, LogoutResponse

router = APIRouter()

login_rate_limiter = RateLimiter()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    key = f"login:{client_ip or payload.username}"
    allowed, _, _ = login_rate_limiter.allow(key)
    if not allowed:
        log_auth_event(db, None, None, "login_rate_limited", client_ip, user_agent, "too many attempts")
        db.commit()
        raise HTTPException(status_code=429, detail="Too many login attempts, try again later")
    user = authenticate_credentials(db, payload.username, payload.password)
    if user is None:
        log_auth_event(db, None, None, "login_failed", client_ip, user_agent, "invalid credentials")
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    roles = [r.name for r in user.roles]
    token = create_jwt(str(user.id), roles)
    log_auth_event(db, user.id, None, "login_success", client_ip, user_agent, None)
    db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    user_id = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = verify_jwt(token)
            subject = payload.get("sub")
            if subject is not None:
                user_id = int(subject)
        except Exception:
            user_id = None
    log_auth_event(db, user_id, None, "logout", client_ip, user_agent, None)
    db.commit()
    return {"message": "Logged out"}

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.domain.schemas import UserCreate, UserUpdate, UserOut
from app.repositories.users import UserRepository
from app.api.deps import get_current_principal, enforce_rate_limit
from app.services.credential_service import CredentialService
from app.domain import models

router = APIRouter()

def require_admin(user) -> None:
    roles = {getattr(r, "name", r) for r in getattr(user, "roles", [])}
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin role required")

@router.get("", response_model=list[UserOut])
def list_users(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user, _ = principal
    require_admin(user)
    return db.query(models.User).order_by(models.User.id).offset(offset).limit(limit).all()

@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, response: Response, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user_repo = UserRepository(db)
    remaining, reset = enforce_rate_limit(principal[0].id)
    existing = user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="User exists")
    user = user_repo.create(payload.email, payload.display_name)
    user_repo.set_roles(user, payload.roles or [])
    db.commit()
    db.refresh(user)
    response.headers["X-RateLimit-Limit"] = str(60)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return user

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, response: Response, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    remaining, reset = enforce_rate_limit(principal[0].id)
    user = UserRepository(db).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    response.headers["X-RateLimit-Limit"] = str(60)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return user

@router.post("/{user_id}/password", status_code=204)
def set_user_password(user_id: int, payload: dict, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user, _ = principal
    require_admin(user)
    password = payload.get("password")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    svc = CredentialService(db)
    svc.set_password(user_id, password)
    db.commit()
    return Response(status_code=204)

@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, response: Response, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    remaining, reset = enforce_rate_limit(principal[0].id)
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    repo.update(user, payload.display_name, payload.is_active)
    if payload.roles is not None:
        repo.set_roles(user, payload.roles)
    db.commit()
    db.refresh(user)
    response.headers["X-RateLimit-Limit"] = str(60)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return user

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, response: Response, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    remaining, reset = enforce_rate_limit(principal[0].id)
    repo = UserRepository(db)
    user = repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    repo.delete(user)
    db.commit()
    response.headers["X-RateLimit-Limit"] = str(60)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return Response(status_code=204)

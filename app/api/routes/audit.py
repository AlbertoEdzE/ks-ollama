from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_principal
from app.domain import models

router = APIRouter()


def require_admin(user) -> None:
    names = {getattr(r, "name", r) for r in getattr(user, "roles", [])}
    if "admin" not in names:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin role required")


@router.get("")
def list_audit(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user, _ = principal
    require_admin(user)
    return db.query(models.AuditLog).order_by(models.AuditLog.occurred_at.desc()).limit(limit).all()

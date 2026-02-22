from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.domain.schemas import CredentialCreate, CredentialSecretOut
from app.services.credential_service import CredentialService
from app.repositories.users import UserRepository
from app.api.deps import get_current_principal, enforce_rate_limit
from app.domain import models

router = APIRouter()

@router.get("")
def list_credentials(user_id: int | None = Query(None), db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    query = db.query(models.Credential)
    if user_id is not None:
        query = query.filter(models.Credential.user_id == user_id)
    items = query.order_by(models.Credential.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "label": c.label,
            "alg": c.alg,
            "revoked": c.revoked,
            "revoked_at": c.revoked_at,
            "created_at": c.created_at,
            "expires_at": c.expires_at,
        }
        for c in items
    ]

@router.post("", response_model=CredentialSecretOut, status_code=201)
def create_credential(payload: CredentialCreate, response: Response, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    remaining, reset = enforce_rate_limit(principal[0].id)
    if UserRepository(db).get(payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    service = CredentialService(db)
    cred_id, plaintext = service.create(payload.user_id, payload.label)
    db.commit()
    response.headers["X-RateLimit-Limit"] = str(60)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return {"credential_id": cred_id, "plaintext": plaintext, "expires_at": None}

@router.post("/{credential_id}/revoke", status_code=204)
def revoke_credential(credential_id: int, response: Response, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    remaining, reset = enforce_rate_limit(principal[0].id)
    service = CredentialService(db)
    ok = service.revoke(credential_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    db.commit()
    response.headers["X-RateLimit-Limit"] = str(60)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    return Response(status_code=204)

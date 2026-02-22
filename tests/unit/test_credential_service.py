from app.services.credential_service import CredentialService
from app.domain import models
from app.db.session import SessionLocal, engine
from app.db.base import Base

def setup_module():
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)

def test_generate_and_hash_secret():
    db = SessionLocal()
    try:
        user = models.User(email="u@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)
        service = CredentialService(db)
        cred_id, plaintext = service.create(user.id, "label")
        assert isinstance(cred_id, int)
        assert isinstance(plaintext, str) and len(plaintext) > 0
        db.commit()
    finally:
        db.close()

from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.domain import models
from app.services.credential_service import CredentialService
import pytest

client = TestClient(app)

def setup_module():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Create admin
        admin = db.query(models.User).filter(models.User.email == "admin@example.com").one_or_none()
        if admin is None:
            admin = models.User(email="admin@example.com", display_name="Admin", is_active=True)
            db.add(admin)
            db.commit()
            db.refresh(admin)
        
        admin_role = db.query(models.Role).filter(models.Role.name == "admin").one_or_none()
        if admin_role is None:
            admin_role = models.Role(name="admin")
            db.add(admin_role)
            db.commit()
        
        if admin_role not in admin.roles:
            admin.roles.append(admin_role)
            db.commit()
            
        service = CredentialService(db)
        service.set_password(admin.id, "admin")
        
        # Create normal user
        user = db.query(models.User).filter(models.User.email == "user@example.com").one_or_none()
        if user is None:
            user = models.User(email="user@example.com", display_name="User", is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            
        service.set_password(user.id, "user")
        db.commit()
    finally:
        db.close()
        
    global ADMIN_HEADERS, USER_HEADERS
    # Login as admin
    r = client.post("/auth/login", json={"username": "admin@example.com", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    ADMIN_HEADERS = {"Authorization": f"Bearer {token}"}
    
    # Login as user
    r = client.post("/auth/login", json={"username": "user@example.com", "password": "user"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    USER_HEADERS = {"Authorization": f"Bearer {token}"}

def teardown_module():
    Base.metadata.drop_all(bind=engine)

def test_list_audit_as_admin():
    r = client.get("/audit", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_list_audit_as_user():
    r = client.get("/audit", headers=USER_HEADERS)
    assert r.status_code == 403
    assert r.json()["detail"] == "Admin role required"

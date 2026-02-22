from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal

client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.domain import models
        from app.services.credential_service import CredentialService

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
        db.commit()
    finally:
        db.close()
    global AUTH_HEADERS
    r = client.post("/auth/login", json={"username": "admin@example.com", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    AUTH_HEADERS = {"Authorization": f"Bearer {token}"}


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_full_flow():
    r = client.post("/users", json={"email": "flow@example.com", "roles": ["user"]}, headers=AUTH_HEADERS)
    assert r.status_code == 201
    uid = r.json()["id"]
    r2 = client.post("/credentials", json={"user_id": uid}, headers=AUTH_HEADERS)
    assert r2.status_code == 201
    cred_id = r2.json()["credential_id"]
    r3 = client.post(f"/credentials/{cred_id}/revoke", headers=AUTH_HEADERS)
    assert r3.status_code == 204

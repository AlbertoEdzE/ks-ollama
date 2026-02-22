from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.domain import models
from app.services.credential_service import CredentialService


client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
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
        u = db.query(models.User).filter(models.User.email == "roles.user@example.com").one_or_none()
        if u is None:
            u = models.User(email="roles.user@example.com", display_name="R User", is_active=True)
            db.add(u)
            db.commit()
            db.refresh(u)
        user_role = db.query(models.Role).filter(models.Role.name == "user").one_or_none()
        if user_role is None:
            user_role = models.Role(name="user")
            db.add(user_role)
            db.commit()
        if user_role not in u.roles:
            u.roles.append(user_role)
            db.commit()
    finally:
        db.close()


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_users_roles_are_strings():
    r = client.post("/auth/login", json={"username": "admin@example.com", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r2 = client.get("/users?limit=50&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data = r2.json()
    assert isinstance(data, list)
    assert all(isinstance(u["roles"], list) for u in data)
    if data:
        for u in data:
            for role in u["roles"]:
                assert isinstance(role, str)

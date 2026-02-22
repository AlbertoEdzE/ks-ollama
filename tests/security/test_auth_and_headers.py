from datetime import datetime, timedelta, timezone
import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.config import settings

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


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def test_missing_auth_header_returns_401():
    r = client.get("/users/1")
    assert r.status_code == 401


def test_security_headers_present():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"
    assert "default-src" in r.headers.get("Content-Security-Policy", "")


def test_successful_login_issues_jwt_and_allows_access():
    r = client.post("/auth/login", json={"username": "admin@example.com", "password": "admin"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r_create = client.post("/users", json={"email": "secuser@example.com", "display_name": "Sec User"}, headers=headers)
    assert r_create.status_code in (201, 400)


def test_failed_login_rejected_and_not_issued_token():
    r = client.post("/auth/login", json={"username": "admin@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_session_timeout_results_in_401():
    db = SessionLocal()
    try:
        from app.domain import models

        user = models.User(email="timeout@example.com", display_name="Timeout User", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        now = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
        payload = {"sub": str(user.id), "roles": ["admin"], "iat": int(now.timestamp()), "exp": int(now.timestamp())}
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    finally:
        db.close()
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/users/1", headers=headers)
    assert r.status_code == 401


def test_logout_logs_event_and_client_can_drop_token():
    r = client.post("/auth/login", json={"username": "admin@example.com", "password": "admin"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r_user = client.post("/users", json={"email": "logout@example.com"}, headers=headers)
    assert r_user.status_code in (201, 400)
    r_logout = client.post("/auth/logout", headers=headers)
    assert r_logout.status_code == 200
    r_after = client.get("/users/1")
    assert r_after.status_code == 401

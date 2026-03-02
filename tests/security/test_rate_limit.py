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


def test_rate_limit_headers_and_enforcement(monkeypatch):
    from app.services.rate_limit import RateLimiter
    
    # Mock RateLimiter to simulate enforcement
    call_count = 0
    def custom_allow(self, key):
        nonlocal call_count
        call_count += 1
        # Allow 5 requests, then block
        if call_count > 5:
            return False, 0, 60
        return True, 10 - call_count, 60
        
    monkeypatch.setattr(RateLimiter, "allow", custom_allow)

    # Trigger rate limit
    exceeded = False
    # We need fewer requests now since we mocked it to fail after 5
    for _ in range(10):
        # Use a protected endpoint
        resp = client.get("/users/1", headers=AUTH_HEADERS)
        if resp.status_code == 429:
            exceeded = True
            break
        # These headers might not be present if we mocked allow directly depending on how the decorator uses it
        # But looking at the code, the decorator likely calls allow() and sets headers based on return values
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers
    assert exceeded

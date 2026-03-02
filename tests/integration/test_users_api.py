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


def test_create_get_user():
    r = client.post("/users", json={"email": "user1@example.com", "display_name": "User 1", "roles": ["user"]}, headers=AUTH_HEADERS)
    assert r.status_code == 201
    uid = r.json()["id"]
    r2 = client.get(f"/users/{uid}", headers=AUTH_HEADERS)
    assert r2.status_code == 200

def test_list_users():
    r = client.get("/users?limit=10&offset=0", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_create_duplicate_user():
    # Setup - ensure user exists
    client.post("/users", json={"email": "dup@example.com", "display_name": "Dup"}, headers=AUTH_HEADERS)
    
    # Test duplicate
    r = client.post("/users", json={"email": "dup@example.com", "display_name": "Dup"}, headers=AUTH_HEADERS)
    assert r.status_code == 400
    assert "User exists" in r.json()["detail"]

def test_get_user_not_found():
    r = client.get("/users/99999", headers=AUTH_HEADERS)
    assert r.status_code == 404

def test_set_user_password():
    # Create user
    r = client.post("/users", json={"email": "pwd@example.com", "display_name": "Pwd"}, headers=AUTH_HEADERS)
    uid = r.json()["id"]
    
    # Set password
    r = client.post(f"/users/{uid}/password", json={"password": "newpass"}, headers=AUTH_HEADERS)
    assert r.status_code == 204
    
    # Verify login
    r = client.post("/auth/login", json={"username": "pwd@example.com", "password": "newpass"})
    assert r.status_code == 200

def test_set_user_password_validation():
    r = client.post("/users/1/password", json={"password": "123"}, headers=AUTH_HEADERS)
    assert r.status_code == 400

def test_update_user():
    # Create user
    r = client.post("/users", json={"email": "upd@example.com", "display_name": "Upd"}, headers=AUTH_HEADERS)
    uid = r.json()["id"]
    
    # Update
    r = client.patch(f"/users/{uid}", json={"display_name": "Updated", "roles": ["admin"]}, headers=AUTH_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["display_name"] == "Updated"
    assert "admin" in data["roles"]

def test_update_user_not_found():
    r = client.patch("/users/99999", json={"display_name": "Upd"}, headers=AUTH_HEADERS)
    assert r.status_code == 404

def test_delete_user():
    # Create user
    r = client.post("/users", json={"email": "del@example.com", "display_name": "Del"}, headers=AUTH_HEADERS)
    uid = r.json()["id"]
    
    # Delete
    r = client.delete(f"/users/{uid}", headers=AUTH_HEADERS)
    assert r.status_code == 204
    
    # Verify deleted
    r = client.get(f"/users/{uid}", headers=AUTH_HEADERS)
    assert r.status_code == 404

def test_delete_user_not_found():
    r = client.delete("/users/99999", headers=AUTH_HEADERS)
    assert r.status_code == 404

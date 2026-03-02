from unittest.mock import MagicMock
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
        
        # Ensure admin role
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

def test_list_models_success(monkeypatch):
    mock_client_cls = MagicMock()
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    mock_instance.list_models.return_value = ["llama2", "mistral"]
    
    monkeypatch.setattr("app.api.routes.ollama.OllamaClient", mock_client_cls)
    
    r = client.get("/ollama/models", headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json() == ["llama2", "mistral"]

def test_list_models_error(monkeypatch):
    mock_client_cls = MagicMock()
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    mock_instance.list_models.side_effect = Exception("Ollama down")
    
    monkeypatch.setattr("app.api.routes.ollama.OllamaClient", mock_client_cls)
    
    r = client.get("/ollama/models", headers=AUTH_HEADERS)
    assert r.status_code == 502
    assert "Ollama error" in r.json()["detail"]

def test_chat_success(monkeypatch):
    mock_client_cls = MagicMock()
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    mock_instance.chat.return_value = "Hello user"
    
    monkeypatch.setattr("app.api.routes.ollama.OllamaClient", mock_client_cls)
    
    payload = {"model": "llama2", "prompt": "Hi"}
    r = client.post("/ollama/chat", json=payload, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json() == {"response": "Hello user"}
    mock_instance.chat.assert_called_with("llama2", "Hi")

def test_embeddings_success(monkeypatch):
    mock_client_cls = MagicMock()
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    mock_instance.embeddings.return_value = [0.1, 0.2]
    
    monkeypatch.setattr("app.api.routes.ollama.OllamaClient", mock_client_cls)
    
    payload = {"model": "llama2", "input": "text"}
    r = client.post("/ollama/embeddings", json=payload, headers=AUTH_HEADERS)
    assert r.status_code == 200
    assert r.json() == {"embedding": [0.1, 0.2]}
    mock_instance.embeddings.assert_called_with("llama2", "text")

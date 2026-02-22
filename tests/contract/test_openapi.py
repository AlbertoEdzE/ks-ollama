from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_openapi_available():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "openapi" in data
    assert "/users" in data["paths"]

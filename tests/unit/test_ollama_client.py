import pytest
from unittest.mock import MagicMock, patch
from app.services.ollama_client import OllamaClient

@patch("app.services.ollama_client.httpx.Client")
def test_ollama_health_success(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    mock_instance.get.return_value.status_code = 200
    
    client = OllamaClient()
    assert client.health() is True
    mock_instance.get.assert_called_with("/")

@patch("app.services.ollama_client.httpx.Client")
def test_ollama_health_failure(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    mock_instance.get.side_effect = Exception("Connection error")
    
    client = OllamaClient()
    assert client.health() is False

@patch("app.services.ollama_client.httpx.Client")
def test_list_models_success(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    
    # Test "models" key format
    mock_instance.get.return_value.json.return_value = {
        "models": [{"name": "llama2"}, {"name": "mistral"}]
    }
    mock_instance.get.return_value.status_code = 200
    
    client = OllamaClient()
    models = client.list_models()
    assert "llama2" in models
    assert "mistral" in models
    mock_instance.get.assert_called_with("/api/tags")

@patch("app.services.ollama_client.httpx.Client")
def test_list_models_alt_format(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    
    # Test "tags" key format and "model" field
    mock_instance.get.return_value.json.return_value = {
        "tags": [{"model": "llama2:latest"}]
    }
    
    client = OllamaClient()
    models = client.list_models()
    assert "llama2:latest" in models

@patch("app.services.ollama_client.httpx.Client")
def test_chat_success(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    
    mock_instance.post.return_value.json.return_value = {"response": "Hello world"}
    mock_instance.post.return_value.status_code = 200
    
    client = OllamaClient()
    response = client.chat("llama2", "Hi")
    assert response == "Hello world"
    mock_instance.post.assert_called_with(
        "/api/generate", 
        json={"model": "llama2", "prompt": "Hi", "stream": False}
    )

@patch("app.services.ollama_client.httpx.Client")
def test_embeddings_success(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    
    mock_instance.post.return_value.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_instance.post.return_value.status_code = 200
    
    client = OllamaClient()
    emb = client.embeddings("llama2", "text")
    assert emb == [0.1, 0.2, 0.3]
    mock_instance.post.assert_called_with(
        "/api/embeddings", 
        json={"model": "llama2", "prompt": "text"}
    )

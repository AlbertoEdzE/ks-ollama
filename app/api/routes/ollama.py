from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_principal, enforce_rate_limit
from app.services.ollama_client import OllamaClient

router = APIRouter()


class ChatRequest(BaseModel):
    model: str
    prompt: str


class ChatResponse(BaseModel):
    response: str


class EmbeddingsRequest(BaseModel):
    model: str
    input: str


class EmbeddingsResponse(BaseModel):
    embedding: list[float]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user, _ = principal
    remaining, reset = enforce_rate_limit(user.id)
    try:
        client = OllamaClient()
        text = client.chat(payload.model, payload.prompt)
        return {"response": text}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")


@router.post("/embeddings", response_model=EmbeddingsResponse)
def embeddings(payload: EmbeddingsRequest, db: Session = Depends(get_db), principal=Depends(get_current_principal)):
    user, _ = principal
    remaining, reset = enforce_rate_limit(user.id)
    try:
        client = OllamaClient()
        vec = client.embeddings(payload.model, payload.input)
        return {"embedding": vec}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

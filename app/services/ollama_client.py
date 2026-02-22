import httpx
from app.config import settings


class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.resolved_ollama_base_url()
        self.client = httpx.Client(base_url=self.base_url, timeout=15.0)

    def health(self) -> bool:
        try:
            r = self.client.get("/")
            return r.status_code < 500
        except Exception:
            return False

    def chat(self, model: str, prompt: str) -> str:
        r = self.client.post("/api/generate", json={"model": model, "prompt": prompt, "stream": False})
        r.raise_for_status()
        data = r.json()
        # Ollama returns {"response": "..."} for /api/generate
        return data.get("response", "")

    def embeddings(self, model: str, input_text: str) -> list[float]:
        r = self.client.post("/api/embeddings", json={"model": model, "prompt": input_text})
        r.raise_for_status()
        data = r.json()
        return data.get("embedding", [])

    def close(self):
        self.client.close()

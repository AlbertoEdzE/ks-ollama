import os
from pydantic import BaseModel

class Settings(BaseModel):
    environment: str = os.getenv("ENVIRONMENT", "local")
    db_user: str = os.getenv("DB_USER", "app")
    db_password: str = os.getenv("DB_PASSWORD", "app")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "app")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_alg: str = os.getenv("JWT_ALG", "HS256")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "")

    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def resolved_ollama_base_url(self) -> str:
        if self.ollama_base_url:
            return self.ollama_base_url
        if self.environment == "prod":
            return "http://ollama.default.svc.cluster.local:11434"
        return "http://localhost:11434"

settings = Settings()

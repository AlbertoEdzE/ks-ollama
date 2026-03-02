import os
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Set environment variables for testing
os.environ["DB_NAME"] = "test_app"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_USER"] = "app"
os.environ["DB_PASSWORD"] = "app"
os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"

@pytest.fixture(autouse=True)
def init_db():
    from app.config import settings
    from app.db.base import Base
    from app.db.session import engine

    settings.rate_limit_per_minute = 10000  # Disable rate limiting for tests
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield

@pytest.fixture(autouse=True)
def disable_rate_limiting(monkeypatch):
    """Disable rate limiting for all tests."""
    from app.services.rate_limit import RateLimiter
    
    def always_allow(self, key):
        return True, 10000, 60
        
    monkeypatch.setattr(RateLimiter, "allow", always_allow)


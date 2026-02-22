import os
import sys
from pathlib import Path
import pytest
from testcontainers.postgres import PostgresContainer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    with PostgresContainer("postgres:15") as pg:
        user = getattr(pg, "username", getattr(pg, "USER", "test"))
        password = getattr(pg, "password", getattr(pg, "PASSWORD", "test"))
        dbname = getattr(pg, "dbname", getattr(pg, "DBNAME", "test"))
        host = pg.get_container_host_ip()
        port = str(pg.get_exposed_port(5432))
        os.environ["DB_USER"] = user
        os.environ["DB_PASSWORD"] = password
        os.environ["DB_HOST"] = host
        os.environ["DB_PORT"] = port
        os.environ["DB_NAME"] = dbname
        os.environ["ENVIRONMENT"] = "local"
        yield

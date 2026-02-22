import os
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session", autouse=True)
def postgres_container():
    with PostgresContainer("postgres:15") as pg:
        os.environ["DB_USER"] = pg.USER
        os.environ["DB_PASSWORD"] = pg.PASSWORD
        os.environ["DB_HOST"] = pg.get_container_host_ip()
        os.environ["DB_PORT"] = str(pg.get_exposed_port(5432))
        os.environ["DB_NAME"] = pg.DBNAME
        os.environ["ENVIRONMENT"] = "local"
        yield

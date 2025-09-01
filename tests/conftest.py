import pytest, pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.infrastructure.config.config import Config


@pytest.fixture(scope="session")
def test_db_config():
    return Config(env_file=".env.test")

@pytest_asyncio.fixture(scope="session")
def async_engine(test_db_config: Config):
    async_engine = create_async_engine(
        url=test_db_config.db.get_database_url(),
        echo = True
    )
    return async_engine


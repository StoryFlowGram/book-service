import pytest, pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from app.infrastructure.config.config import Config
from app.infrastructure.database.base import Base
from app.infrastructure.models.book_model import Book
from app.infrastructure.models.chapter_model import Chapter

@pytest.fixture(scope="session")
def test_db_config():
    return Config(env_file=".env.test")

@pytest_asyncio.fixture(scope="function")
def async_engine(test_db_config: Config):
    engine = create_async_engine(
        url=test_db_config.db.get_database_url(),
        echo = True
    )
    return engine

@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database(async_engine: AsyncEngine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(async_engine: AsyncEngine):
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()



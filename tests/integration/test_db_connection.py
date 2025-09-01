import pytest
from app.infrastructure.database.base import Base
from app.infrastructure.models.book_model import Book
from app.infrastructure.models.chapter_model import Chapter


@pytest.mark.asyncio
async def test_db_connection(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(Base.metadata.drop_all)
    
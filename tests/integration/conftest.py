import pytest_asyncio

from app.infrastructure.repositories.book_repositories import BookRepository
from app.domain.entity.book import Book as BookDomain

@pytest_asyncio.fixture
async def test_book(session):
    repo = BookRepository(session)
    book = BookDomain(
        id=None,
        title="Test Title",
        author="Test Author",
        description="Test Description",
        pic_url="http://example.com/pic.jpg",
        difficulty= 1
    )
    add_book = await repo.add(book)
    yield add_book
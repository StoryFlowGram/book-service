import pytest

from app.infrastructure.repositories.chapter_repositories import ChapterRepository
from app.domain.entity.chapter import Chapter as ChapterDomain


@pytest.mark.asyncio
async def test_add_chapter(session, test_book):
    repo = ChapterRepository(session)
    chapter = ChapterDomain(
        id=None,
        book_id=test_book.id,
        title="Test Title",
        order_number=1,
        word_count=100,
        s3_url="https://example.com/test.txt"
    )
    added_chapter = await repo.add(chapter)
    assert added_chapter.title == "Test Title"
    assert added_chapter.book_id == test_book.id
    assert added_chapter.order_number == 1
    assert added_chapter.word_count == 100
    assert added_chapter.s3_url == "https://example.com/test.txt"

@pytest.mark.asyncio
async def test_get_chapter(session, test_book):
    repo = ChapterRepository(session)
    chapter = ChapterDomain(
        id=None,
        book_id=test_book.id,
        title="Test Title",
        order_number=1,
        word_count=100,
        s3_url="https://example.com/test.txt"
    )
    add_chapter = await repo.add(chapter)
    assert add_chapter.id is not None
    get_chapter = await repo.get_chapter_by_id(add_chapter.id)

    assert get_chapter.title == "Test Title"
    assert get_chapter.book_id == test_book.id
    assert get_chapter.order_number == 1
    assert get_chapter.word_count == 100
    assert get_chapter.s3_url == "https://example.com/test.txt"

@pytest.mark.asyncio
async def test_delete_chapter(session, test_book):
    repo = ChapterRepository(session)
    chapter = ChapterDomain(
        id=None,
        book_id=test_book.id,
        title="Test Title",
        order_number=1,
        word_count=100,
        s3_url="https://example.com/test.txt"
    )
    add_chapter = await repo.add(chapter)
    assert add_chapter.id is not None
    await repo.delete(add_chapter.id)
    deleted_chapter = await repo.get_chapter_by_id(add_chapter.id)
    assert deleted_chapter is None
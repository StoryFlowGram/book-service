import pytest

from app.infrastructure.repositories.book_repositories import BookRepository
from app.domain.entity.book import Book as BookDomain
from app.domain.enum.difficulty import Difficulty


@pytest.mark.asyncio
async def test_add_book(session):
    repo = BookRepository(session)
    book = BookDomain(
        id=None,
        title="Test Title",
        author="Test Author",
        description="Test Description",
        pic_url="http://example.com/pic.jpg",
        difficulty= 1
    )
    added_book = await repo.add(book)
    assert added_book.title == "Test Title"
    assert added_book.author == "Test Author"
    assert added_book.description == "Test Description"
    assert added_book.pic_url == "http://example.com/pic.jpg"
    assert added_book.difficulty == 1
    assert added_book.id is not None


@pytest.mark.asyncio
async def test_get_book(session):
    repo = BookRepository(session)
    book = BookDomain(
        id=None,
        title="Test Title 2",
        author="Test Author 2",
        description="Test Description 2",
        pic_url="http://example.com/pic.jpg",
        difficulty= 1
    )

    add_book = await repo.add(book)
    assert add_book.id is not None
    get_book = await repo.get(add_book.id)

    assert get_book.title == "Test Title 2"
    assert get_book.author == "Test Author 2"
    assert get_book.description == "Test Description 2"
    assert get_book.pic_url == "http://example.com/pic.jpg"
    assert get_book.difficulty == 1


@pytest.mark.asyncio
async def test_list_books(session):
    repo = BookRepository(session)
    book1 = BookDomain(
        id=None,
        title="Test Title 3",
        author="Test Author 3",
        description="Test Description 3",
        pic_url="http://example.com/pic1.jpg",
        difficulty= 1
    )

    book2 = BookDomain(
        id=None,
        title="Test Title 4",
        author="Test Author 4",
        description="Test Description 4",
        pic_url="http://example.com/pic2.jpg",
        difficulty= 2
    )

    await repo.add(book1)
    await repo.add(book2)

    books = await repo.list()

    assert len(books) == 2

    assert books[0].title == "Test Title 3"
    assert books[0].author == "Test Author 3"
    assert books[0].description == "Test Description 3"
    assert books[0].pic_url == "http://example.com/pic1.jpg"
    assert books[0].difficulty == 1

    assert books[1].title == "Test Title 4"
    assert books[1].author == "Test Author 4"
    assert books[1].description == "Test Description 4"
    assert books[1].pic_url == "http://example.com/pic2.jpg"
    assert books[1].difficulty == 2




@pytest.mark.asyncio
async def test_update_book(session):
    repo = BookRepository(session)
    book = BookDomain(
        id=None,
        title="Test Title 5",
        author="Test Author 5",
        description="Test Description 5",
        pic_url="http://example.com/pic.jpg",
        difficulty= 1
    )

    add_book = await repo.add(book)
    assert add_book.id is not None
    update_book = await repo.update(add_book.id, "Test Title 6", "Test Author 6", "Test Description 6", "http://example.com/pic.jpg", 1)
    assert update_book.title == "Test Title 6"
    assert update_book.author == "Test Author 6"
    assert update_book.description == "Test Description 6"
    assert update_book.pic_url == "http://example.com/pic.jpg"
    assert update_book.difficulty == 1


@pytest.mark.asyncio
async def test_delete_book(session):
    repo = BookRepository(session)
    book = BookDomain(
        id=None,
        title="Test Title 7",
        author="Test Author 7",
        description="Test Description 7",
        pic_url="http://example.com/pic.jpg",
        difficulty= 5
    )
    add_book = await repo.add(book)
    assert add_book.id is not None
    await repo.delete(add_book.id)
    deleted_book = await repo.get(add_book.id)
    assert deleted_book is None


@pytest.mark.asyncio
async def test_find_by_title_author(session):
    repo = BookRepository(session)
    book = BookDomain(
        id=None,
        title="Test Title 8",
        author="Test Author 8",
        description="Test Description 8",
        pic_url="http://example.com/pic.jpg",
        difficulty= 5
    )

    add_book = await repo.add(book)
    assert add_book.id is not None
    find_book = await repo.find_by_title_author("Test Title 8", "Test Author 8")

    assert find_book.title == "Test Title 8"
    assert find_book.author == "Test Author 8"
    assert find_book.description == "Test Description 8"
    assert find_book.pic_url == "http://example.com/pic.jpg"
    assert find_book.difficulty == 5
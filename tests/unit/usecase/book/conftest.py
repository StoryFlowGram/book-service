import pytest
import pytest_asyncio
from typing import Dict, Any, cast
from pytest_mock import MockerFixture
from app.application.usecase.book.delete_book import DeleteBookUsecase
from app.application.usecase.book.update_book import UpdateBookUsecase
from app.application.usecase.book.get_book import GetBookUsecase
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.usecase.book.create_book import CreateBookUsecase
from app.application.usecase.book.list_book import BookListUsecase
from app.application.usecase.book.find_by_title_book import FindByTitleBookUsecase
from app.domain.entity.book import Book

@pytest_asyncio.fixture
async def book_protocol_mock(mocker: MockerFixture) -> AbstractBookProtocol:

    mock = mocker.AsyncMock(spec=AbstractBookProtocol, autospec=True)
    return cast(AbstractBookProtocol, mock)

@pytest_asyncio.fixture
async def create_book_usecase(book_protocol_mock: AbstractBookProtocol) -> CreateBookUsecase:
    return CreateBookUsecase(book_protocol_mock)

@pytest_asyncio.fixture
async def find_by_title_usecase(book_protocol_mock: AbstractBookProtocol) -> FindByTitleBookUsecase:
    return FindByTitleBookUsecase(book_protocol_mock)


@pytest_asyncio.fixture
async def get_book_usecase(book_protocol_mock: AbstractBookProtocol) -> CreateBookUsecase:
    return GetBookUsecase(book_protocol_mock)


@pytest_asyncio.fixture
async def delete_book_usecase(book_protocol_mock: AbstractBookProtocol) -> DeleteBookUsecase:
    return DeleteBookUsecase(book_protocol_mock)

@pytest_asyncio.fixture
async def list_book_usecase(book_protocol_mock: AbstractBookProtocol) -> CreateBookUsecase:
    return BookListUsecase(book_protocol_mock)

@pytest_asyncio.fixture
async def update_book_usecase(book_protocol_mock: AbstractBookProtocol) -> CreateBookUsecase:
    return UpdateBookUsecase(book_protocol_mock)

@pytest.fixture
def sample_book_data() -> Dict[str, Any]:
    return {
        "id": 1,
        "title": "Test Book",
        "author": "Test Author",
        "description": "A" * 100,
        "pic_url": "http://example.com/image.jpg",
        "difficulty": 3
    }


@pytest.fixture
def sample_book_entity(sample_book_data: Dict[str, Any]) -> Book:
    return Book(**sample_book_data)


@pytest.fixture
def sample_book_list(sample_book_data: Dict[str, Any]) -> list[Book]:
    book1 = Book(**sample_book_data)

    book2_data = sample_book_data.copy()
    book2_data["id"] = 2
    book2_data["title"] = "Test Book 2"
    book2 = Book(**book2_data)

    book3_data = sample_book_data.copy()
    book3_data["id"] = 3
    book3_data["title"] = "Test Book 3"
    book3 = Book(**book3_data)


    return [book1, book2, book3]
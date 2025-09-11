import pytest
import pytest_asyncio
from typing import Dict, Any, cast
from pytest_mock import MockerFixture

from app.application.usecase.chapter.add_chapter import AddChapterUsecase
from app.application.usecase.chapter.delete_chapter import DeleteChapterUsecase
from app.application.usecase.chapter.get_chapter_by_id import GetChapterByIdUsecase
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.domain.protocols.book_protocol import AbstractBookProtocol 
from app.domain.entity.chapter import Chapter
from app.domain.entity.book import Book 

@pytest_asyncio.fixture
async def chapter_protocol_mock(mocker: MockerFixture) -> AbstractChapterProtocol:
    mock = mocker.AsyncMock(spec=AbstractChapterProtocol, autospec=True)
    return cast(AbstractChapterProtocol, mock)

@pytest_asyncio.fixture
async def book_protocol_mock(mocker: MockerFixture) -> AbstractBookProtocol:
    mock = mocker.AsyncMock(spec=AbstractBookProtocol, autospec=True)
    return cast(AbstractBookProtocol, mock)

@pytest_asyncio.fixture
async def add_chapter_usecase(chapter_protocol_mock: AbstractChapterProtocol, book_protocol_mock: AbstractBookProtocol) -> AddChapterUsecase:
    return AddChapterUsecase(chapter_protocol_mock, book_protocol_mock)

@pytest_asyncio.fixture
async def delete_chapter_usecase(chapter_protocol_mock: AbstractChapterProtocol) -> DeleteChapterUsecase:
    return DeleteChapterUsecase(chapter_protocol_mock)

@pytest_asyncio.fixture
async def get_chapter_by_id_usecase(chapter_protocol_mock: AbstractChapterProtocol) -> GetChapterByIdUsecase:
    return GetChapterByIdUsecase(chapter_protocol_mock)

@pytest.fixture
def sample_chapter_data() -> Dict[str, Any]:
    return {
        "id": 1,
        "book_id": 1,
        "title": "Test Chapter",
        "order_number": 1,
        "word_count": 200,
        "s3_url": "http://s3.example.com/chapter.txt",
    }

@pytest.fixture
def sample_chapter_entity(sample_chapter_data: Dict[str, Any]) -> Chapter:
    return Chapter(**sample_chapter_data)

@pytest.fixture
def sample_book_entity() -> Book:
    return Book(
        id=1,
        title="Test Book",
        author="Test Author",
        description="A" * 100,
        pic_url="http://example.com/image.jpg",
        difficulty=3 
    )
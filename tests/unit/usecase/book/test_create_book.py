import pytest
from app.application.dto.book.book import BookDTO
from app.application.usecase.book.create_book import CreateBookUsecase
from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol

@pytest.mark.asyncio
async def test_create_book_success(
    create_book_usecase: CreateBookUsecase,
    book_protocol_mock: AbstractBookProtocol,
    sample_book_entity: Book
) -> None:
    book_protocol_mock.find_by_title_author.return_value = None
    book_protocol_mock.add.return_value = sample_book_entity

    result = await create_book_usecase(sample_book_entity)
    book_protocol_mock.find_by_title_author.assert_called_once_with(
        sample_book_entity.title, sample_book_entity.author
    )
    book_protocol_mock.add.assert_called_once_with(sample_book_entity)

    assert isinstance(result, BookDTO)
    assert result.title == sample_book_entity.title

@pytest.mark.asyncio
async def test_create_book_already_exists(
    create_book_usecase: CreateBookUsecase,
    book_protocol_mock: AbstractBookProtocol,
    sample_book_entity: Book
) -> None:
    book_protocol_mock.find_by_title_author.return_value = sample_book_entity
    with pytest.raises(Exception, match="Книга с таким названием и автором уже существует"):
        await create_book_usecase(sample_book_entity)
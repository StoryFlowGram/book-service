import pytest
from app.application.usecase.book.find_by_title_book import FindByTitleBookUsecase
from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol


@pytest.mark.asyncio
async def test_find_by_title_success(
    find_by_title_usecase: FindByTitleBookUsecase,
    sample_book_entity: Book,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.find_by_title_author.return_value = sample_book_entity

    result = await find_by_title_usecase(sample_book_entity.title, sample_book_entity.author)

    book_protocol_mock.find_by_title_author.assert_called_once_with(
        sample_book_entity.title, sample_book_entity.author
    )
    assert result == sample_book_entity


@pytest.mark.asyncio
async def test_find_by_title_not_found(
    find_by_title_usecase: FindByTitleBookUsecase,
    sample_book_entity: Book,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.find_by_title_author.return_value = None

    with pytest.raises(Exception, match="Книга с таким названием не найдена"):
        await find_by_title_usecase(sample_book_entity.title, sample_book_entity.author)

    book_protocol_mock.find_by_title_author.assert_called_once_with(
        sample_book_entity.title, sample_book_entity.author
    )
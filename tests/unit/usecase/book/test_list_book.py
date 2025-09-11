import pytest
from app.application.usecase.book.list_book import BookListUsecase
from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.dto.book.book import BookDTO
from app.domain.enum.difficulty import Difficulty


@pytest.mark.asyncio
async def test_book_list_success(
    list_book_usecase: BookListUsecase,
    sample_book_list: list[Book],
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.list.return_value = sample_book_list

    result = await list_book_usecase(limit=20, cursor=None)

    book_protocol_mock.list.assert_called_once_with(20, None)
    assert len(result) == len(sample_book_list)
    assert all(isinstance(dto, BookDTO) for dto in result)
    assert result[0].id == sample_book_list[0].id
    assert result[0].title == sample_book_list[0].title
    assert result[0].difficulty == Difficulty.B1 

    book_protocol_mock.list.reset_mock()
    book_protocol_mock.list.return_value = sample_book_list
    result_with_cursor = await list_book_usecase(limit=10, cursor="next_cursor_token")

    book_protocol_mock.list.assert_called_once_with(10, "next_cursor_token")
    assert len(result_with_cursor) == len(sample_book_list)


@pytest.mark.asyncio
async def test_book_list_not_found(
    list_book_usecase: BookListUsecase,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.list.return_value = []

    with pytest.raises(Exception, match="Книги не найдены"):
        await list_book_usecase(limit=20, cursor=None)

    book_protocol_mock.list.assert_called_once_with(20, None)

    book_protocol_mock.list.return_value = None

    with pytest.raises(Exception, match="Книги не найдены"):
        await list_book_usecase(limit=20, cursor=None)
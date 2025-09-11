import pytest
from app.application.usecase.book.update_book import UpdateBookUsecase
from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.dto.book.book import BookDTO


@pytest.mark.asyncio
async def test_update_book_success(
    update_book_usecase: UpdateBookUsecase,
    sample_book_entity: Book,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = sample_book_entity
    updated_book = Book(**{**sample_book_entity.__dict__, "title": "Updated Title"})
    book_protocol_mock.update.return_value = updated_book

    long_description = "A" * 100
    result = await update_book_usecase(
        book_id=sample_book_entity.id,
        title="Updated Title",
        author=None,
        description=long_description,
        pic_url=None,
        difficulty=None
    )

    book_protocol_mock.get.assert_called_once_with(sample_book_entity.id)
    book_protocol_mock.update.assert_called_once_with(
        sample_book_entity.id,
        "Updated Title",
        None,
        long_description,
        None,
        None
    )
    assert result == BookDTO(
        id=updated_book.id,
        title=updated_book.title,
        author=updated_book.author,
        description=long_description, 
        pic_url=updated_book.pic_url,
        difficulty=updated_book.difficulty
    )


@pytest.mark.asyncio
async def test_update_book_not_found(
    update_book_usecase: UpdateBookUsecase,
    sample_book_entity: Book,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = None

    with pytest.raises(Exception, match="Книга не найдена"):
        await update_book_usecase(
            book_id=sample_book_entity.id,
            title=None,
            author=None,
            description="A" * 100,
            pic_url=None,
            difficulty=None
        )


@pytest.mark.asyncio
async def test_update_book_invalid_description(
    update_book_usecase: UpdateBookUsecase,
    sample_book_entity: Book,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = sample_book_entity

    with pytest.raises(Exception, match="Описание должно быть длиннее 100 символов"):
        await update_book_usecase(
            book_id=sample_book_entity.id,
            title=None,
            author=None,
            description="Short",
            pic_url=None,
            difficulty=None
        )

    with pytest.raises(Exception, match="Описание должно быть длиннее 100 символов"):
        await update_book_usecase(
            book_id=sample_book_entity.id,
            title=None,
            author=None,
            description=None,
            pic_url=None,
            difficulty=None
        )
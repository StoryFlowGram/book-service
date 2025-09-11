import pytest
from app.application.usecase.chapter.add_chapter import AddChapterUsecase
from app.domain.entity.chapter import Chapter
from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.dto.chapter.chapter import ChapterDTO


@pytest.mark.asyncio
async def test_add_chapter_success(
    add_chapter_usecase: AddChapterUsecase,
    sample_chapter_entity: Chapter,
    sample_book_entity: Book,
    chapter_protocol_mock: AbstractChapterProtocol,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = sample_book_entity
    chapter_protocol_mock.add.return_value = sample_chapter_entity

    result = await add_chapter_usecase(sample_chapter_entity)

    book_protocol_mock.get.assert_called_once_with(sample_chapter_entity.book_id)
    chapter_protocol_mock.add.assert_called_once_with(sample_chapter_entity)
    assert isinstance(result, ChapterDTO)
    assert result.id == sample_chapter_entity.id
    assert result.book_id == sample_chapter_entity.book_id
    assert result.title == sample_chapter_entity.title
    assert result.order_number == sample_chapter_entity.order_number
    assert result.word_count == sample_chapter_entity.word_count
    assert result.s3_url == sample_chapter_entity.s3_url


@pytest.mark.asyncio
async def test_add_chapter_book_not_found(
    add_chapter_usecase: AddChapterUsecase,
    sample_chapter_entity: Chapter,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = None

    with pytest.raises(Exception, match=f"Книга с id {sample_chapter_entity.book_id} не найдена"):
        await add_chapter_usecase(sample_chapter_entity)

    book_protocol_mock.get.assert_called_once_with(sample_chapter_entity.book_id)


@pytest.mark.asyncio
async def test_add_chapter_empty_title(
    add_chapter_usecase: AddChapterUsecase,
    sample_chapter_entity: Chapter,
    sample_book_entity: Book,
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = sample_book_entity
    invalid_chapter = Chapter(
        id=sample_chapter_entity.id,
        book_id=sample_chapter_entity.book_id,
        title="",
        order_number=sample_chapter_entity.order_number,
        word_count=sample_chapter_entity.word_count,
        s3_url=sample_chapter_entity.s3_url
    )

    with pytest.raises(Exception, match="Название главы не может быть пустым"):
        await add_chapter_usecase(invalid_chapter)

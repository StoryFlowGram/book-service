import pytest
from app.application.usecase.chapter.get_chapters_by_book_id import GetChapterByIdUsecase
from app.domain.entity.chapter import Chapter
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.dto.chapter.chapter import ChapterDTO


@pytest.mark.asyncio
async def test_get_chapter_by_id_success(
    get_chapter_by_id_usecase: GetChapterByIdUsecase,
    sample_chapter_entity: Chapter,
    chapter_protocol_mock: AbstractChapterProtocol
) -> None:
    chapter_protocol_mock.get_chapter_by_id.return_value = sample_chapter_entity

    result = await get_chapter_by_id_usecase(sample_chapter_entity.id)

    chapter_protocol_mock.get_chapter_by_id.assert_called_once_with(sample_chapter_entity.id)
    assert isinstance(result, ChapterDTO)
    assert result.id == sample_chapter_entity.id
    assert result.book_id == sample_chapter_entity.book_id
    assert result.title == sample_chapter_entity.title
    assert result.order_number == sample_chapter_entity.order_number
    assert result.word_count == sample_chapter_entity.word_count
    assert result.s3_url == sample_chapter_entity.s3_url


@pytest.mark.asyncio
async def test_get_chapter_by_id_not_found(
    get_chapter_by_id_usecase: GetChapterByIdUsecase,
    chapter_protocol_mock: AbstractChapterProtocol
) -> None:
    chapter_protocol_mock.get_chapter_by_id.return_value = None

    with pytest.raises(Exception, match="Глава с id 999 не найдена"):
        await get_chapter_by_id_usecase(999)

    chapter_protocol_mock.get_chapter_by_id.assert_called_once_with(999)
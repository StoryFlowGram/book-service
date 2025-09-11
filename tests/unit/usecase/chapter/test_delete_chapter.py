import pytest
from app.application.usecase.chapter.delete_chapter import DeleteChapterUsecase
from app.domain.entity.chapter import Chapter
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol


@pytest.mark.asyncio
async def test_delete_chapter_success(
    delete_chapter_usecase: DeleteChapterUsecase,
    sample_chapter_entity: Chapter,
    chapter_protocol_mock: AbstractChapterProtocol
) -> None:
    chapter_protocol_mock.get_chapter_by_id.return_value = sample_chapter_entity
    chapter_protocol_mock.delete.return_value = True 

    result = await delete_chapter_usecase(sample_chapter_entity.id)

    chapter_protocol_mock.get_chapter_by_id.assert_called_once_with(sample_chapter_entity.id)
    chapter_protocol_mock.delete.assert_called_once_with(sample_chapter_entity.id)
    assert result is True 


@pytest.mark.asyncio
async def test_delete_chapter_not_found(
    delete_chapter_usecase: DeleteChapterUsecase,
    chapter_protocol_mock: AbstractChapterProtocol
) -> None:
    chapter_protocol_mock.get_chapter_by_id.return_value = None

    with pytest.raises(Exception, match="Глава не найдена. Не существует"):
        await delete_chapter_usecase(999) 

    chapter_protocol_mock.get_chapter_by_id.assert_called_once_with(999)
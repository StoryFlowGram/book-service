from app.domain.entity.chapter import Chapter
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.interfaces.storage import AbstractStorage
from app.application.dto.chapter.chapter import ChapterContentDTO


class GetChapterContent:
    def __init__(self, chapter_repository: AbstractChapterProtocol, storage: AbstractStorage):
        self.chapter_repository = chapter_repository
        self.storage = storage

    async def __call__(self, chapter_id: int) -> str:
        chapter: Chapter | None = await self.chapter_repository.get_chapter_by_id(chapter_id)
        if chapter is None:
            raise ValueError(f"Глава с id {chapter_id} не найдена")
        
        if not chapter.s3_url:
            raise ValueError(f"Глава с id {chapter_id} не имеет s3_url")
        
        content = await self.storage.get_object_content(chapter.s3_url)
        return content
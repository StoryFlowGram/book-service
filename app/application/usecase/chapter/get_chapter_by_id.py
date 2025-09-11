from app.domain.entity.chapter import Chapter
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.dto.chapter.chapter import ChapterDTO

class GetChapterByIdUsecase:
    def __init__(self, chapter_repository: AbstractChapterProtocol):
        self.chapter_repository = chapter_repository

    async def __call__(self, chapter_id: int):
        chapter = await self.chapter_repository.get_chapter_by_id(chapter_id)
        if chapter is None:
            raise Exception(f"Глава с id {chapter_id} не найдена")
        return ChapterDTO(
            id=chapter.id,
            book_id=chapter.book_id,
            title=chapter.title,
            order_number=chapter.order_number,
            word_count=chapter.word_count,
            s3_url=chapter.s3_url
        )
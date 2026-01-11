from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.dto.chapter.chapter import ChapterDTO

class GetChapterByIdUsecase:
    def __init__(self, chapter_repository: AbstractChapterProtocol):
        self.chapter_repository = chapter_repository

    async def __call__(self, book_id: int):
        chapter = await self.chapter_repository.get_chapters_by_book_id(book_id)
        if chapter is None:
            return []
        
        return [ChapterDTO(
            id=chapter.id,
            book_id=chapter.book_id,
            title=chapter.title,
            order_number=chapter.order_number,
            word_count=chapter.word_count,
            s3_url=chapter.s3_url
        )for chapter in chapter]
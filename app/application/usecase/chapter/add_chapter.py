from app.domain.entity.chapter import Chapter
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.dto.chapter.chapter import ChapterDTO



class AddChapterUsecase:
    def __init__(self, chapter_repository: AbstractChapterProtocol, book_repository: AbstractBookProtocol):
        self.chapter_repository = chapter_repository
        self.book_repository = book_repository

    async def __call__(self,chapter: Chapter):
        parent = await self.book_repository.get(chapter.book_id)
        if parent is None:
            raise Exception(f"Книга с id {chapter.book_id} не найдена")
        if not chapter.title or not chapter.title.strip():
            raise Exception("Название главы не может быть пустым")
        add_chapter = await self.chapter_repository.add(chapter)
        return ChapterDTO(
            id=add_chapter.id,
            book_id=add_chapter.book_id,
            title=add_chapter.title,
            order_number=add_chapter.order_number,
            word_count=add_chapter.word_count,
            s3_url=add_chapter.s3_url
        )
import os
import logging
from app.domain.entity.book import Book as BookEntity
from app.domain.entity.chapter import Chapter as ChapterEntity
from app.domain.enum.difficulty import Difficulty
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.interfaces.storage import AbstractStorage
from app.application.service.epub_service import EpubService

logger = logging.getLogger(__name__)

class ProcessBookUsecase:
    def __init__(
        self,
        book_repo: AbstractBookProtocol,
        chapter_repo: AbstractChapterProtocol,
        storage: AbstractStorage,
        epub_service: EpubService
    ):
        self.book_repo = book_repo
        self.chapter_repo = chapter_repo
        self.storage = storage
        self.epub_service = epub_service

    async def __call__(self, object_name: str, difficulty: int | None):
        local_path = None
        try:
            logger.info(f"UseCase: Начинаем процесс {object_name}")
            
            local_path = await self.storage.download_to_temp(object_name)
            
            metadata = await self.epub_service.read_metadata(local_path)
            
            pic_url = None
            if metadata["cover_content"]:
                pic_url = await self.storage.upload_cover(metadata["title"], metadata["cover_content"])

            book_entity = BookEntity(
                id=0,
                title=metadata["title"],
                author=metadata["author"],
                description=metadata["description"],
                pic_url=pic_url,
                difficulty=Difficulty(difficulty) if difficulty else None
            )
            created_book = await self.book_repo.add(book_entity)
            logger.info(f"Книга созданная: {created_book.title} (ID: {created_book.id})")

            chapters_data = await self.epub_service.extract_chapters(metadata["book_obj"])
            
            for chap in chapters_data:
                s3_chapter_url = await self.storage.upload_chapter_text(
                    created_book.id, 
                    chap["order_number"], 
                    chap["text"]
                )
            
                chapter_entity = ChapterEntity(
                    id=0,
                    book_id=created_book.id,
                    title=chap["title"],
                    order_number=chap["order_number"],
                    word_count=chap["word_count"],
                    s3_url=s3_chapter_url
                )
                await self.chapter_repo.add(chapter_entity)

            logger.info(f"Все главы добавлены в книгу {created_book.id}")
            return {"status": "success", "book_id": created_book.id}

        except Exception as e:
            logger.error(f"Ошибка UseCase: {e}")
            raise e
            
        finally:
            if local_path and os.path.exists(local_path):
                os.unlink(local_path)
            
            await self.storage.delete_object(object_name)
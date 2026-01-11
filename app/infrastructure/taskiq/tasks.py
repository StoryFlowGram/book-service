import logging
from taskiq import TaskiqDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.taskiq.broker import broker

from app.infrastructure.repositories.book_repositories import BookRepository
from app.infrastructure.repositories.chapter_repositories import ChapterRepository
from app.infrastructure.s3.s3_storage import S3Storage


from app.application.usecase.book.process_book import ProcessBookUsecase
from app.application.service.epub_service import EpubService

logger = logging.getLogger(__name__)

@broker.task
async def process_epub(
    object_name: str,
    difficulty: int | None = None,
    session: AsyncSession = TaskiqDepends(get_session)
) -> dict:
    s3_storage = S3Storage()
    book_repo = BookRepository(session)
    chapter_repo = ChapterRepository(session)
    
    epub_service = EpubService()
    
    usecase = ProcessBookUsecase(
        book_repo=book_repo,
        chapter_repo=chapter_repo,
        storage=s3_storage,
        epub_service=epub_service
    )

    try:
        result = await usecase(object_name, difficulty)
        return result

    except Exception as e:
        logger.error(f"Критическая ошибка в обработке книги: {e}")
        raise e
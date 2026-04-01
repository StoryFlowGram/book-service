import logging

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqDepends

from app.application.service.epub_service import EpubService
from app.application.usecase.book.process_book import ProcessBookUsecase
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.book_repositories import BookRepository
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository
from app.infrastructure.repositories.chapter_repositories import ChapterRepository
from app.infrastructure.s3.s3_storage import S3Storage
from app.infrastructure.taskiq.broker import broker

logger = logging.getLogger(__name__)


@broker.task
async def process_epub(
    object_name: str,
    difficulty: int | None = None,
    upload_id: str | None = None,
    session: AsyncSession = TaskiqDepends(get_session),
) -> dict:
    s3_storage = S3Storage()
    book_repo = BookRepository(session)
    chapter_repo = ChapterRepository(session)
    upload_job_repo = BookUploadJobRepository(session)

    epub_service = EpubService()

    usecase = ProcessBookUsecase(
        book_repo=book_repo,
        chapter_repo=chapter_repo,
        storage=s3_storage,
        epub_service=epub_service,
    )

    try:
        result = await usecase(object_name, difficulty)
        if upload_id:
            await upload_job_repo.set_completed(upload_id, result.get("book_id"))
        return result
    except Exception as error:
        if upload_id:
            await upload_job_repo.set_failed(upload_id, str(error))
        logger.error(f"Taskiq process_epub failed: {error}")
        raise

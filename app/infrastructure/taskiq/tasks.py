from taskiq import TaskiqDepends
from ebooklib import epub, ITEM_DOCUMENT, ITEM_IMAGE 
from bs4 import BeautifulSoup
import logging
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.book_repositories import BookRepository
from app.infrastructure.repositories.chapter_repositories import ChapterRepository
from app.infrastructure.s3.s3_storage import S3Storage
from app.application.usecase.book.create_book import CreateBookUsecase
from app.application.usecase.chapter.add_chapter import AddChapterUsecase
from app.domain.entity.book import Book as BookEntity
from app.domain.entity.chapter import Chapter as ChapterEntity
from app.domain.enum.difficulty import Difficulty
from app.infrastructure.taskiq.broker import broker

logger = logging.getLogger(__name__)

@broker.task
async def process_epub(
    object_name: str,
    difficulty: int | None = None,
    session: AsyncSession = TaskiqDepends(get_session)
) -> dict:
    s3_storage = S3Storage()
    local_epub_path = None
    loop = asyncio.get_running_loop()

    book_repo = BookRepository(session)
    chapter_repo = ChapterRepository(session)
    create_book_usecase = CreateBookUsecase(book_repo)
    add_chapter_usecase = AddChapterUsecase(chapter_repo, book_repo)

    try:
        logger.info(f"Начинаю обработку файла: {object_name}")
        local_epub_path = await s3_storage.download_to_temp(object_name)
        logger.info(f"Файл загружен во временную директорию: {local_epub_path}")

        book = await loop.run_in_executor(None, epub.read_epub, local_epub_path)


        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'Unknown Title'
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else 'Unknown Author'
        description = book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else 'No description'

        pic_url = None
        cover_item = book.get_item_with_id('cover') or next((item for item in book.get_items_of_type(ITEM_IMAGE) if 'cover' in item.file_name.lower()), None)
        if cover_item:
            cover_content = await loop.run_in_executor(None, cover_item.get_content)
            pic_url = await s3_storage.upload_cover(title, cover_content)

        book_entity = BookEntity(
            id=0, 
            title=title,
            author=author,
            description=description,
            pic_url=pic_url,
            difficulty=Difficulty(difficulty) if difficulty else None
        )
        
        
        created_book_domain = await book_repo.add(book_entity) 
        
        book_id = created_book_domain.id
        logger.info(f"Книга '{title}' создана в БД с ID: {book_id}")

        order_number = 1
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            if not item.is_chapter():
                continue

            html_content = await loop.run_in_executor(None, item.get_content)
            soup = BeautifulSoup(html_content.decode('utf-8', errors='ignore'), 'html.parser')
            chapter_text = soup.get_text(separator='\n', strip=True)

            if len(chapter_text) < 100:
                continue

            chapter_title = soup.find(['h1', 'h2', 'h3']).text.strip() if soup.find(['h1', 'h2', 'h3']) else f"Chapter {order_number}"
            word_count = len(chapter_text.split())

            s3_url = await s3_storage.upload_chapter_text(book_id, order_number, chapter_text)

            chapter_entity = ChapterEntity(
                id=0,  
                book_id=book_id,
                title=chapter_title,
                order_number=order_number,
                word_count=word_count,
                s3_url=s3_url
            )
            
            await chapter_repo.add(chapter_entity)
            order_number += 1

        logger.info(f"Все главы для книги '{title}' (ID: {book_id}) успешно добавлены.")
        return {"status": "success", "message": f"Книга '{title}' (ID: {book_id}) успешно добавлена"}

    except Exception as e:
        logger.error(f"Ошибка при обработке EPUB файла {object_name}: {e}")
        raise
    finally:
        if local_epub_path and os.path.exists(local_epub_path):
            await loop.run_in_executor(None, os.unlink, local_epub_path)
            logger.info(f"Локальный файл удален: {local_epub_path}")
        
        await s3_storage.delete_object(object_name)
        logger.info(f"Временный файл в S3 удален: {object_name}")
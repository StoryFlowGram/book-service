from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.infrastructure.s3.s3_storage import S3Storage
from app.infrastructure.repositories.book_repositories import BookRepository
from app.infrastructure.repositories.chapter_repositories import ChapterRepository
from app.infrastructure.database.session import get_session




async def book_protocol(session: AsyncSession = Depends(get_session)) -> BookRepository:
    return BookRepository(session)


async def chapter_protocol(session: AsyncSession = Depends(get_session)) -> ChapterRepository:
    return ChapterRepository(session)

async def storage(storage = Depends(S3Storage)) -> S3Storage:
    return storage
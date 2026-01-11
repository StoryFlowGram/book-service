from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger


from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.domain.entity.chapter import Chapter as ChapterDomain
from app.infrastructure.models.chapter_model import Chapter as ChapterModel
from app.infrastructure.mappers.chapter_mapper import orm_to_domain, domain_to_orm


class ChapterRepository(AbstractChapterProtocol):
    def __init__(self, session_factory: AsyncSession):
        self.session_factory = session_factory

    async def add(self, chapter: ChapterDomain):
        orm = domain_to_orm(chapter)
        self.session_factory.add(orm)
        await self.session_factory.commit()
        await self.session_factory.refresh(orm)
        return orm_to_domain(orm)
    
    #Должен выдавать все главы по id книги
    async def get_chapters_by_book_id(self, book_id: int):
        stmt = select(ChapterModel).where(ChapterModel.book_id == book_id).order_by(ChapterModel.order_number)
        result = await self.session_factory.execute(stmt)
        orm = result.scalars().unique().all()
        logger.info(f"get_chapter_by_id вот что в нем {orm}")
        if not orm:
            return []
        return [orm_to_domain(chapter) for chapter in orm]
    

    async def get_chapter_by_id(self, chapter_id: int):
        stmt = select(ChapterModel).where(ChapterModel.id == chapter_id)
        result = await self.session_factory.execute(stmt)
        orm = result.scalars().one_or_none()
        if not orm:
            return None
        return orm_to_domain(orm)
    
    async def delete(self, chapter_id: int):
        stmt = delete(ChapterModel).where(ChapterModel.id == chapter_id)
        await self.session_factory.execute(stmt)
        await self.session_factory.commit()
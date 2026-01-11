from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.domain.entity.book import Book as BookDomain
from app.infrastructure.models.book_model import Book as BookModel
from app.infrastructure.mappers.book_mapper import orm_to_domain, domain_to_orm


class BookRepository(AbstractBookProtocol):
    def __init__(self, session_factory: AsyncSession):
        self.session_factory = session_factory

    async def add(self, book: BookDomain):
        orm = domain_to_orm(book)
        self.session_factory.add(orm)
        await self.session_factory.commit()
        await self.session_factory.refresh(orm)
        return orm_to_domain(orm)
    
    async def get(self, book_id: int):
        stmt = select(BookModel).where(BookModel.id == book_id)
        result = await self.session_factory.execute(stmt)
        orm = result.scalars().one_or_none()
        if not orm:
            return None
        return orm_to_domain(orm)
    
    async def list(self, limit: int , cursor: Optional[str] = None):
        stmt = select(BookModel)
        if cursor:
            stmt = stmt.where(BookModel.id > cursor)
        stmt = stmt.order_by(BookModel.id.asc())
        stmt = stmt.limit(limit)
        result = await self.session_factory.execute(stmt)
        rows = result.scalars().all()
        return [orm_to_domain(row)
            for row in rows
        ]
    
    async def update(self, book_id: int, title: Optional[str], author: Optional[str], description: Optional[str], pic_url: Optional[str],  difficulty: Optional[str]):
        stmt = update(BookModel).where(BookModel.id == book_id).values(
            title=title, author=author, description=description, pic_url=pic_url, difficulty=difficulty
        )
        await self.session_factory.execute(stmt)
        await self.session_factory.commit()

        stmt_select = select(BookModel).where(BookModel.id == book_id)
        result = await self.session_factory.execute(stmt_select)
        orm = result.scalars().one()
        return orm_to_domain(orm)

    async def delete(self, book_id: int):
        stmt = delete(BookModel).where(BookModel.id == book_id)
        await self.session_factory.execute(stmt)
        await self.session_factory.commit()

    async def find_by_title_author(self, title, author):
        stmt = select(BookModel).where(
            BookModel.title == title,
            BookModel.author == author
            )
        result = await self.session_factory.execute(stmt)
        orm = result.scalar_one_or_none()
        if not orm:
            return None
        return orm_to_domain(orm)
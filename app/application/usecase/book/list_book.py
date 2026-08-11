from typing import Optional

from app.application.dto.book.book import BookDTO
from app.domain.protocols.book_protocol import AbstractBookProtocol


class BookListUsecase:
    def __init__(self, protocol: AbstractBookProtocol):
        self.protocol = protocol

    async def __call__(self, limit: int = 20, cursor: Optional[int] = None):
        books = await self.protocol.list(limit, cursor)
        if not books:
            return {
                "items": [],
                "next_cursor": None,
            }

        next_cursor = books[-1].id
        if len(books) < limit:
            next_cursor = None

        book_dtos = [
            BookDTO(
                id=book.id,
                title=book.title,
                author=book.author,
                description=book.description,
                pic_url=book.pic_url,
                difficulty=book.difficulty,
            )
            for book in books
        ]
        return {
            "items": book_dtos,
            "next_cursor": next_cursor,
        }

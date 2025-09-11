from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.dto.book.book import BookDTO
from typing import Optional


class BookListUsecase:
    def __init__(self, protocol: AbstractBookProtocol):
        self.protocol = protocol

    async def __call__(self, limit: int = 20, cursor: Optional[str] = None):
        get_list_book = await self.protocol.list(limit, cursor)
        if not get_list_book:
            raise Exception("Книги не найдены")

        return [
            BookDTO(
                id=book.id,
                title=book.title,
                author=book.author,
                description=book.description,
                pic_url=book.pic_url,
                difficulty=book.difficulty
            ) for book in get_list_book
        ]
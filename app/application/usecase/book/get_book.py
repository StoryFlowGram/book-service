from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.dto.book.book import BookDTO



class GetBookUsecase:
    def __init__(self, protocol: AbstractBookProtocol):
        self.protocol = protocol

    async def __call__(self, book_id: int):
        get_book = await self.protocol.get(book_id)
        if not get_book:
            raise Exception("Книга не найдена")
        
        return BookDTO(
            id=get_book.id,
            title=get_book.title,
            author=get_book.author,
            description=get_book.description,
            pic_url=get_book.pic_url,
            difficulty=get_book.difficulty
        )
    
from app.domain.entity.book import Book
from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.dto.book.book import BookDTO


class CreateBookUsecase:
    def __init__(self, protocol: AbstractBookProtocol):
        self.protocol = protocol

    async def __call__(self, book: Book):
        exist = await self.protocol.find_by_title_author(book.title, book.author)
        if exist:
            raise Exception("Книга с таким названием и автором уже существует")
        
        if len(book.description) < 100:
            raise Exception("Описание должно быть длиннее 100 символов")
        
        add_book = await self.protocol.add(book)
        return BookDTO(
            id=add_book.id,
            title=add_book.title,
            author=add_book.author,
            description=add_book.description,
            pic_url=add_book.pic_url,
            difficulty=add_book.difficulty
        )

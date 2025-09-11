from app.domain.protocols.book_protocol import AbstractBookProtocol
from app.application.dto.book.book import BookDTO
from typing import Optional


class UpdateBookUsecase:
    def __init__(self, protocol: AbstractBookProtocol):
        self.protocol = protocol

    async def __call__(
        self, 
        book_id: int, 
        title: Optional[str], 
        author: Optional[str], 
        description: Optional[str], 
        pic_url: Optional[str],  
        difficulty: Optional[str]
    ) -> BookDTO: 
        
        existing = await self.protocol.get(book_id)
        if not existing:
            raise Exception("Книга не найдена")
        if description is None or len(description) < 100:
            raise Exception("Описание должно быть длиннее 100 символов")
        updated_book = await self.protocol.update(book_id, title, author, description, pic_url, difficulty)

        return BookDTO(
            id=updated_book.id,
            title=updated_book.title,
            author=updated_book.author,
            description=updated_book.description,
            pic_url=updated_book.pic_url,
            difficulty=updated_book.difficulty
        )
from app.domain.protocols.book_protocol import AbstractBookProtocol


class FindByTitleBookUsecase:
    def __init__(self, protocol:AbstractBookProtocol):
        self.protocol = protocol


    async def __call__(self, title: str, author: str):
        check_book = await self.protocol.find_by_title_author(title, author)
        if not check_book:
            raise Exception("Книга с таким названием не найдена")
        return check_book
from app.domain.protocols.book_protocol import AbstractBookProtocol


class DeleteBookUsecase:
    def __init__(self, protocol: AbstractBookProtocol):
        self.protocol = protocol

    async def __call__(self, book_id: int):
        check_exist = await self.protocol.get(book_id)
        if not check_exist:
            raise Exception("Книга не найдена")
        return self.protocol.delete(book_id)
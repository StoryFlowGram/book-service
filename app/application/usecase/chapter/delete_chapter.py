from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from loguru import logger


class DeleteChapterUsecase:
    def __init__(self, chapter_repository: AbstractChapterProtocol):
        self.chapter_repository = chapter_repository
    
    async def __call__(self, chapter_id: int):
        check_exist = await self.chapter_repository.get_chapter_by_id(chapter_id)
        logger.info(check_exist)
        if not check_exist:
            raise Exception("Глава не найдена. Не существует")
        return await self.chapter_repository.delete(chapter_id)
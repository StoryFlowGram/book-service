from app.domain.protocols.chapter_protocol import AbstractChapterProtocol
from app.application.interfaces.storage import AbstractStorage

class GetChapterContentUsecase:
    def __init__(self, chapter_repository: AbstractChapterProtocol, storage: AbstractStorage):
        self.chapter_repository = chapter_repository
        self.storage = storage

    async def __call__(self, chapter_id: int) -> str:
        chapter = await self.chapter_repository.get_chapter_by_id(chapter_id)
        
        if chapter is None:
            raise ValueError(f"Глава с id {chapter_id} не найдена в базе данных")
        
        if not chapter.s3_url:
            raise ValueError(f"У главы {chapter.title} отсутствует ссылка на контент (s3_url)")
        
        try:
            content = await self.storage.get_object_content(chapter.s3_url)
            return content
        except Exception as e:
            raise ValueError(f"Ошибка получения файла из хранилища: {str(e)}")
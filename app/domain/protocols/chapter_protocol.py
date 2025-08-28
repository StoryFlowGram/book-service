from abc import abstractmethod
from app.domain.entity.chapter import Chapter



class ChapterProtocol:
    @abstractmethod
    async def add(self, chapter: Chapter):
        ...

    @abstractmethod
    async def get_chapter_by_id(self, chapter_id: int):
        ...

    @abstractmethod
    async def update(self, chapter: Chapter):
        ...

    @abstractmethod
    async def delete(self, chapter_id: int):
        ...
from abc import abstractmethod
from app.domain.entity.chapter import Chapter



class AbstractChapterProtocol:
    @abstractmethod
    async def add(self, chapter: Chapter):
        ...

    @abstractmethod
    async def get_chapters_by_book_id(self, book_id: int) -> list | list[Chapter]:
        ...

    @abstractmethod
    async def get_chapter_by_id(self, chapter_id: int) -> Chapter:
        ...

    @abstractmethod
    async def update(self, chapter: Chapter):
        ...

    @abstractmethod
    async def delete(self, chapter_id: int):
        ...
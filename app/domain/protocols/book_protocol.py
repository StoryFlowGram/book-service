from abc import ABC, abstractmethod
from typing import Optional


from app.domain.enum.difficulty import Difficulty

class AbstractBookProtocol(ABC):
    @abstractmethod
    async def add(self):
        ...

    @abstractmethod
    async def get(self, book_id: int):
        ...
    
    @abstractmethod
    async def list(self, limit: int = 20, cursor: Optional[int] = None):
        ...

    @abstractmethod
    async def update(
        self, 
        book_id: int, 
        title: Optional[str],
        author: Optional[str],
        description: Optional[str],
        pic_url: Optional[str],
        difficulty: Optional[Difficulty]
    ):
        ...

    @abstractmethod
    async def delete(self, book_id: int):
        ...

    @abstractmethod
    async def find_by_title_author(self, title: str, author: str):
        ...
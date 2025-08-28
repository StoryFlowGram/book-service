from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entity.book import Book


class BookProtocol(ABC):
    @abstractmethod
    async def add(self):
        ...

    @abstractmethod
    async def get(self, book_id: int):
        ...
    
    @abstractmethod
    async def list(self):
        ...

    @abstractmethod
    async def update(self, book_id: int):
        ...

    @abstractmethod
    async def delete(self, book_id: int):
        ...

    @abstractmethod
    async def find_by_title_author(self, title: str, author: str):
        ...
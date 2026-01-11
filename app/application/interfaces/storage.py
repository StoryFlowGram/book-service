from abc import ABC, abstractmethod
from typing import BinaryIO

class AbstractStorage(ABC):
    @abstractmethod
    async def get_object_content(self, s3_url: str) -> str:
        pass


    @abstractmethod
    async def upload_fileobj(self, file: BinaryIO, object_name: str) -> str:
        pass

    @abstractmethod
    async def delete_object(self, object_name: str) -> None:
        pass

    @abstractmethod
    async def download_to_temp(self, object_name: str) -> str:
        pass

    @abstractmethod
    async def upload_cover(self, title: str, cover_content: bytes) -> str:
        pass


    @abstractmethod
    async def upload_chapter_text(self, book_id: int, order_number: int, text: str) -> str:
        pass
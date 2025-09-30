from abc import ABC, abstractmethod

class AbstractStorage(ABC):
    @abstractmethod
    async def get_object_content(self, s3_url: str) -> str:
        pass
from abc import ABC, abstractmethod

class AbstractEpubProcessor(ABC):
    @abstractmethod
    async def send_to_process(self, object_name: str, difficulty: int | None) -> None:
        pass
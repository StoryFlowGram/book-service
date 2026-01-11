from app.application.interfaces.task_broker import AbstractEpubProcessor
from app.infrastructure.taskiq.tasks import process_epub

class TaskiqEpubAdapter(AbstractEpubProcessor):
    async def send_to_process(self, object_name: str, difficulty: int | None) -> None:
        if difficulty is not None:
            await process_epub.kiq(object_name, difficulty)
        else:
            await process_epub.kiq(object_name)
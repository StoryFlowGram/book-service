import logging

from app.application.interfaces.task_broker import AbstractEpubProcessor
from app.infrastructure.taskiq.broker import broker, startup_broker_with_retry
from app.infrastructure.taskiq.tasks import process_epub

logger = logging.getLogger(__name__)


class TaskQueueUnavailableError(RuntimeError):
    pass


class TaskiqEpubAdapter(AbstractEpubProcessor):
    async def _ensure_broker_started(self) -> None:
        # taskiq_aio_pika requires startup to create write channel before `.kiq(...)`.
        if getattr(broker, "write_channel", None) is None:
            await startup_broker_with_retry()

    async def send_to_process(
        self,
        object_name: str,
        difficulty: int | None,
        upload_id: str | None = None,
    ) -> None:
        try:
            await self._ensure_broker_started()
            if difficulty is not None:
                await process_epub.kiq(object_name, difficulty, upload_id)
            else:
                await process_epub.kiq(object_name, None, upload_id)
        except Exception as error:
            logger.exception(
                "Failed to publish TaskIQ job to broker. object_name=%s upload_id=%s",
                object_name,
                upload_id,
            )
            raise TaskQueueUnavailableError(
                "Cannot send task to queue. Check TASKIQ_BROKER_URL and RabbitMQ availability."
            ) from error

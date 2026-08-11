import asyncio
import logging

from taskiq.middlewares import SmartRetryMiddleware
from taskiq_aio_pika import AioPikaBroker

from app.infrastructure.config.config import Config

config = Config()
logger = logging.getLogger(__name__)

broker = AioPikaBroker(
    url=config.taskiq.taskiq_broker_url,
).with_middlewares(
    SmartRetryMiddleware(
        default_retry_count=3,
        default_delay=5,
    )
)


async def startup_broker_with_retry(
    retries: int | None = None,
    delay_seconds: float | None = None,
) -> None:
    if getattr(broker, "write_channel", None) is not None:
        return

    max_attempts = retries or config.taskiq.startup_connect_retries
    backoff_seconds = delay_seconds or config.taskiq.startup_connect_delay_seconds

    for attempt in range(1, max_attempts + 1):
        try:
            await broker.startup()
            logger.info("Taskiq broker connected on attempt %s", attempt)
            return
        except Exception:
            if attempt >= max_attempts:
                logger.exception(
                    "Taskiq broker startup failed after %s attempts. broker_url=%s",
                    max_attempts,
                    config.taskiq.taskiq_broker_url,
                )
                raise

            logger.warning(
                "Taskiq broker connection attempt %s/%s failed. Retrying in %.1fs",
                attempt,
                max_attempts,
                backoff_seconds,
            )
            await asyncio.sleep(backoff_seconds)


from app.infrastructure.taskiq import tasks  # noqa: E402,F401

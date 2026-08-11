import json
import logging
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum

import aio_pika
from aio_pika import DeliveryMode, Message

logger = logging.getLogger(__name__)


class SearchIndexBookEventPublisher:
    def __init__(
        self,
        rabbitmq_url: str | None = None,
        queue_name: str | None = None,
    ):
        self.rabbitmq_url = (rabbitmq_url or os.getenv("RABBITMQ_URL") or "").strip()
        if not self.rabbitmq_url:
            raise ValueError("RABBITMQ_URL must be set for SearchIndexBookEventPublisher")
        self.queue_name = (queue_name or os.getenv("SEARCH_BOOK_EVENTS_QUEUE") or "sfg.book-search-updates").strip()

    async def publish_created(self, book_payload: dict | object) -> None:
        payload = self._to_payload(book_payload)
        await self._publish(event_type="book.created", book_id=int(payload["id"]), payload=payload)

    async def publish_updated(self, book_payload: dict | object) -> None:
        payload = self._to_payload(book_payload)
        await self._publish(event_type="book.updated", book_id=int(payload["id"]), payload=payload)

    async def publish_deleted(self, book_id: int) -> None:
        await self._publish(event_type="book.deleted", book_id=int(book_id), payload=None)

    async def _publish(self, event_type: str, book_id: int, payload: dict | None) -> None:
        body = json.dumps(
            {
                "event_type": event_type,
                "event_version": 1,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "book_id": book_id,
                "payload": payload,
            },
            ensure_ascii=False,
        ).encode("utf-8")

        connection = await aio_pika.connect_robust(self.rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(self.queue_name, durable=True)
            await channel.default_exchange.publish(
                Message(
                    body=body,
                    content_type="application/json",
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue_name,
            )

        logger.info(
            "Published search index event. event_type=%s book_id=%s queue=%s",
            event_type,
            book_id,
            self.queue_name,
        )

    def _to_payload(self, book_payload: dict | object) -> dict:
        if isinstance(book_payload, dict):
            payload = dict(book_payload)
        elif is_dataclass(book_payload):
            payload = asdict(book_payload)
        else:
            payload = {
                "id": getattr(book_payload, "id", None),
                "title": getattr(book_payload, "title", None),
                "author": getattr(book_payload, "author", None),
                "description": getattr(book_payload, "description", None),
                "pic_url": getattr(book_payload, "pic_url", None),
                "cover_url": getattr(book_payload, "cover_url", None),
                "difficulty": getattr(book_payload, "difficulty", None),
            }

        difficulty = payload.get("difficulty")
        if isinstance(difficulty, Enum):
            payload["difficulty"] = difficulty.value
        elif difficulty is not None:
            payload["difficulty"] = int(difficulty)

        if payload.get("description") is None:
            payload["description"] = ""

        return payload

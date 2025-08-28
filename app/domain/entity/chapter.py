from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Chapter:
    id: UUID
    book_id: UUID
    title: str
    order: int
    word_count: int
    s3_url: str
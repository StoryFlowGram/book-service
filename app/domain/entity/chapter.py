from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    id: int
    book_id: int
    title: str
    order_number: int
    word_count: int
    s3_url: str
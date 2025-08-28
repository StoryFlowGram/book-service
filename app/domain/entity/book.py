from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from app.domain.enum.difficulty import Difficulty


@dataclass(frozen=True)
class Book:
    id: UUID
    title: str
    author: str
    description: str
    pic_url: str
    s3_url: str
    difficulty: Optional[Difficulty]
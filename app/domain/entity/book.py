from dataclasses import dataclass
from typing import Optional

from app.domain.enum.difficulty import Difficulty


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str
    description: str
    pic_url: str
    difficulty: Optional[Difficulty]
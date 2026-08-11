from dataclasses import dataclass
from typing import Optional
from app.domain.enum.difficulty import Difficulty


@dataclass(frozen=True)
class BookDTO:
    title: str
    author: str
    description: str
    pic_url: Optional[str]
    id: Optional[int]
    difficulty: Optional[Difficulty]
    cover_url: Optional[str] = None

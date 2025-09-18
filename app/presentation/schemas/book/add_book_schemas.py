from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.domain.enum.difficulty import Difficulty


class AddBookResponseSchema(BaseModel):
    id: int
    title: str
    author: str
    description: str
    pic_url: str
    difficulty: Optional[Difficulty] = None

    model_config = ConfigDict(from_attributes=True)


class AddBookRequestSchema(BaseModel):
    title: str
    author: str
    description: str
    pic_url: str
    difficulty: Optional[Difficulty] = None

    model_config = ConfigDict(from_attributes=True)
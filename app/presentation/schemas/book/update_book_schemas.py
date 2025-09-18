from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.domain.enum.difficulty import Difficulty


class UpdateBookRequestSchema(BaseModel):
    title: str
    author: str
    description: str
    pic_url: str
    difficulty: Optional[Difficulty]

    model_config = ConfigDict(from_attributes=True)


class UpdateBookResponseSchema(BaseModel):
    id: int
    title: str
    author: str
    description: str
    pic_url: str
    difficulty: Optional[Difficulty]

    model_config = ConfigDict(from_attributes=True)
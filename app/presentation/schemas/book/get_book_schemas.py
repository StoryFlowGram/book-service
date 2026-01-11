from typing import Optional
from pydantic import BaseModel





class GetBookResponseSchemas(BaseModel):
    id: int
    title: str
    author: str
    description: str
    pic_url: str


class GetBookListResponse(BaseModel):
    items: list[GetBookResponseSchemas]
    next_cursor: Optional[int]
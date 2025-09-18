from pydantic import BaseModel




class GetBookResponseSchemas(BaseModel):
    id: int
    title: str
    author: str
    description: str
    pic_url: str
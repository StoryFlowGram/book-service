from pydantic import BaseModel, ConfigDict


class GetChapterResponseSchemas(BaseModel):
    id: int
    book_id: int
    title: str
    order_number: int
    word_count: int
    s3_url: str
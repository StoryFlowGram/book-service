from pydantic import BaseModel, ConfigDict


class AddChapterRequestSchema(BaseModel):
    book_id: int
    title: str
    order_number: int
    word_count: int
    s3_url: str

    model_config = ConfigDict(from_attributes=True)

class AddChapterResponseSchema(BaseModel):
    id: int
    book_id: int
    title: str
    order_number: int
    word_count: int
    s3_url: str

    model_config = ConfigDict(from_attributes=True)
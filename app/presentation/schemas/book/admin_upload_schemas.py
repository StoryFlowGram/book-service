from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UploadInitRequestSchema(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    difficulty: int | None = Field(default=None, ge=1, le=6)


class UploadJobResponseSchema(BaseModel):
    upload_id: str
    original_filename: str
    object_name: str | None
    difficulty: int | None
    status: str
    created_by_user_id: int
    result_book_id: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadJobListResponseSchema(BaseModel):
    items: list[UploadJobResponseSchema]

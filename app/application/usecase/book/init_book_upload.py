import uuid

from app.infrastructure.models.book_upload_job_model import BookUploadJob
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository


class InitBookUploadUsecase:
    def __init__(self, job_repo: BookUploadJobRepository):
        self.job_repo = job_repo

    async def __call__(
        self,
        filename: str,
        difficulty: int | None,
        created_by_user_id: int,
    ) -> BookUploadJob:
        normalized_filename = filename.strip()
        if not normalized_filename:
            raise ValueError("Filename is required")

        if not normalized_filename.lower().endswith(".epub"):
            raise ValueError("Only EPUB files are allowed")

        upload_id = str(uuid.uuid4())
        return await self.job_repo.create(
            upload_id=upload_id,
            original_filename=normalized_filename,
            difficulty=difficulty,
            created_by_user_id=created_by_user_id,
        )

from app.infrastructure.models.book_upload_job_model import BookUploadJob
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository


class ListBookUploadsUsecase:
    def __init__(self, job_repo: BookUploadJobRepository):
        self.job_repo = job_repo

    async def __call__(self, limit: int = 20) -> list[BookUploadJob]:
        normalized_limit = max(1, min(limit, 100))
        return await self.job_repo.list_recent(limit=normalized_limit)

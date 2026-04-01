from app.infrastructure.models.book_upload_job_model import BookUploadJob
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository


class GetBookUploadUsecase:
    def __init__(self, job_repo: BookUploadJobRepository):
        self.job_repo = job_repo

    async def __call__(self, upload_id: str) -> BookUploadJob:
        job = await self.job_repo.get_by_upload_id(upload_id)
        if not job:
            raise LookupError("Upload job not found")
        return job

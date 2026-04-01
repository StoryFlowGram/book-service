import os

from fastapi import UploadFile

from app.application.interfaces.storage import AbstractStorage
from app.application.interfaces.task_broker import AbstractEpubProcessor
from app.domain.enum.upload_job_status import UploadJobStatus
from app.infrastructure.models.book_upload_job_model import BookUploadJob
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository


class CompleteBookUploadUsecase:
    def __init__(
        self,
        job_repo: BookUploadJobRepository,
        storage: AbstractStorage,
        processor: AbstractEpubProcessor,
    ):
        self.job_repo = job_repo
        self.storage = storage
        self.processor = processor

    async def __call__(
        self,
        upload_id: str,
        file: UploadFile,
        requested_by_user_id: int,
    ) -> BookUploadJob:
        job = await self.job_repo.get_by_upload_id(upload_id)
        if not job:
            raise LookupError("Upload job not found")

        if job.created_by_user_id != requested_by_user_id:
            raise PermissionError("This upload job belongs to another admin")

        if job.status == UploadJobStatus.COMPLETED.value:
            raise ValueError("Upload job is already completed")

        allowed_statuses = {
            UploadJobStatus.INITIALIZED.value,
            UploadJobStatus.FAILED.value,
        }
        if job.status not in allowed_statuses:
            raise ValueError(f"Upload job cannot be completed from status '{job.status}'")

        if not file.filename or not file.filename.lower().endswith(".epub"):
            raise ValueError("Only EPUB files are allowed")

        max_upload_size_bytes = int(os.getenv("BOOK_UPLOAD_MAX_SIZE_BYTES", str(50 * 1024 * 1024)))
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size <= 0:
            raise ValueError("Uploaded file is empty")
        if file_size > max_upload_size_bytes:
            raise ValueError(f"EPUB file is too large. Max size is {max_upload_size_bytes} bytes")

        object_name = f"temp_epubs/{upload_id}.epub"

        try:
            file.file.seek(0)
            await self.storage.upload_fileobj(file.file, object_name)
            job = await self.job_repo.set_processing(upload_id, object_name)
            await self.processor.send_to_process(
                object_name=object_name,
                difficulty=job.difficulty if job else None,
                upload_id=upload_id,
            )
        except Exception as error:
            await self.job_repo.set_failed(upload_id, str(error))
            await self.storage.delete_object(object_name)
            raise

        refreshed_job = await self.job_repo.get_by_upload_id(upload_id)
        if not refreshed_job:
            raise LookupError("Upload job disappeared after completion step")
        return refreshed_job

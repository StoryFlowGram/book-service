from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enum.upload_job_status import UploadJobStatus
from app.infrastructure.models.book_upload_job_model import BookUploadJob


class BookUploadJobRepository:
    def __init__(self, session_factory: AsyncSession):
        self.session_factory = session_factory

    async def create(
        self,
        *,
        upload_id: str,
        original_filename: str,
        difficulty: int | None,
        created_by_user_id: int,
    ) -> BookUploadJob:
        job = BookUploadJob(
            upload_id=upload_id,
            original_filename=original_filename,
            difficulty=difficulty,
            created_by_user_id=created_by_user_id,
            status=UploadJobStatus.INITIALIZED.value,
        )
        self.session_factory.add(job)
        await self.session_factory.commit()
        await self.session_factory.refresh(job)
        return job

    async def get_by_upload_id(self, upload_id: str) -> BookUploadJob | None:
        stmt = select(BookUploadJob).where(BookUploadJob.upload_id == upload_id)
        result = await self.session_factory.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> list[BookUploadJob]:
        stmt = select(BookUploadJob).order_by(BookUploadJob.created_at.desc()).limit(limit)
        result = await self.session_factory.execute(stmt)
        return list(result.scalars().all())

    async def set_processing(self, upload_id: str, object_name: str) -> BookUploadJob | None:
        job = await self.get_by_upload_id(upload_id)
        if not job:
            return None

        job.object_name = object_name
        job.status = UploadJobStatus.PROCESSING.value
        job.error_message = None
        job.updated_at = datetime.now(timezone.utc)

        await self.session_factory.commit()
        await self.session_factory.refresh(job)
        return job

    async def set_completed(self, upload_id: str, book_id: int | None) -> BookUploadJob | None:
        job = await self.get_by_upload_id(upload_id)
        if not job:
            return None

        job.status = UploadJobStatus.COMPLETED.value
        job.error_message = None
        job.result_book_id = book_id
        job.updated_at = datetime.now(timezone.utc)

        await self.session_factory.commit()
        await self.session_factory.refresh(job)
        return job

    async def set_failed(self, upload_id: str, error_message: str) -> BookUploadJob | None:
        job = await self.get_by_upload_id(upload_id)
        if not job:
            return None

        job.status = UploadJobStatus.FAILED.value
        job.error_message = error_message[:4000]
        job.updated_at = datetime.now(timezone.utc)

        await self.session_factory.commit()
        await self.session_factory.refresh(job)
        return job

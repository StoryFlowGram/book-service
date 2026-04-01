from io import BytesIO
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import UploadFile

from app.application.usecase.book.complete_book_upload import CompleteBookUploadUsecase
from app.application.usecase.book.init_book_upload import InitBookUploadUsecase
from app.domain.enum.upload_job_status import UploadJobStatus


@pytest.mark.asyncio
async def test_init_upload_success(mocker):
    job_repo = mocker.AsyncMock()
    expected_job = SimpleNamespace(upload_id="generated")
    job_repo.create.return_value = expected_job
    usecase = InitBookUploadUsecase(job_repo)

    result = await usecase(filename="my_book.epub", difficulty=3, created_by_user_id=42)

    assert result is expected_job
    called_kwargs = job_repo.create.call_args.kwargs
    UUID(called_kwargs["upload_id"])
    assert called_kwargs["original_filename"] == "my_book.epub"
    assert called_kwargs["difficulty"] == 3
    assert called_kwargs["created_by_user_id"] == 42


@pytest.mark.asyncio
async def test_init_upload_requires_epub(mocker):
    job_repo = mocker.AsyncMock()
    usecase = InitBookUploadUsecase(job_repo)

    with pytest.raises(ValueError, match="Only EPUB files are allowed"):
        await usecase(filename="my_book.pdf", difficulty=2, created_by_user_id=7)

    job_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_complete_upload_success(mocker):
    job_repo = mocker.AsyncMock()
    storage = mocker.AsyncMock()
    processor = mocker.AsyncMock()
    usecase = CompleteBookUploadUsecase(job_repo=job_repo, storage=storage, processor=processor)

    job = SimpleNamespace(
        upload_id="upload-1",
        created_by_user_id=100,
        status=UploadJobStatus.INITIALIZED.value,
        difficulty=4,
    )
    job_repo.get_by_upload_id.side_effect = [job, job]
    job_repo.set_processing.return_value = job

    file = UploadFile(filename="book.epub", file=BytesIO(b"fake-epub-data"))

    result = await usecase(upload_id="upload-1", file=file, requested_by_user_id=100)

    assert result is job
    storage.upload_fileobj.assert_called_once()
    job_repo.set_processing.assert_called_once_with("upload-1", "temp_epubs/upload-1.epub")
    processor.send_to_process.assert_called_once_with(
        object_name="temp_epubs/upload-1.epub",
        difficulty=4,
        upload_id="upload-1",
    )
    storage.delete_object.assert_not_called()


@pytest.mark.asyncio
async def test_complete_upload_blocks_other_admin(mocker):
    job_repo = mocker.AsyncMock()
    storage = mocker.AsyncMock()
    processor = mocker.AsyncMock()
    usecase = CompleteBookUploadUsecase(job_repo=job_repo, storage=storage, processor=processor)

    job_repo.get_by_upload_id.return_value = SimpleNamespace(
        upload_id="upload-2",
        created_by_user_id=200,
        status=UploadJobStatus.INITIALIZED.value,
        difficulty=2,
    )
    file = UploadFile(filename="book.epub", file=BytesIO(b"fake-epub-data"))

    with pytest.raises(PermissionError, match="belongs to another admin"):
        await usecase(upload_id="upload-2", file=file, requested_by_user_id=201)

    storage.upload_fileobj.assert_not_called()
    processor.send_to_process.assert_not_called()


@pytest.mark.asyncio
async def test_complete_upload_marks_failed_when_queue_fails(mocker):
    job_repo = mocker.AsyncMock()
    storage = mocker.AsyncMock()
    processor = mocker.AsyncMock()
    processor.send_to_process.side_effect = RuntimeError("broker unavailable")
    usecase = CompleteBookUploadUsecase(job_repo=job_repo, storage=storage, processor=processor)

    job = SimpleNamespace(
        upload_id="upload-3",
        created_by_user_id=300,
        status=UploadJobStatus.INITIALIZED.value,
        difficulty=5,
    )
    job_repo.get_by_upload_id.return_value = job
    job_repo.set_processing.return_value = job

    file = UploadFile(filename="book.epub", file=BytesIO(b"fake-epub-data"))

    with pytest.raises(RuntimeError, match="broker unavailable"):
        await usecase(upload_id="upload-3", file=file, requested_by_user_id=300)

    job_repo.set_failed.assert_called_once()
    storage.delete_object.assert_called_once_with("temp_epubs/upload-3.epub")

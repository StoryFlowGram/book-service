import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.usecase.book.complete_book_upload import CompleteBookUploadUsecase
from app.application.usecase.book.create_book import CreateBookUsecase
from app.application.usecase.book.delete_book import DeleteBookUsecase
from app.application.usecase.book.find_by_title_book import FindByTitleBookUsecase
from app.application.usecase.book.get_book import GetBookUsecase
from app.application.usecase.book.get_book_upload import GetBookUploadUsecase
from app.application.usecase.book.init_book_upload import InitBookUploadUsecase
from app.application.usecase.book.list_book import BookListUsecase
from app.application.usecase.book.list_book_uploads import ListBookUploadsUsecase
from app.application.usecase.book.update_book import UpdateBookUsecase
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository
from app.infrastructure.s3.s3_storage import S3Storage
from app.infrastructure.taskiq.taskiq_adapter import TaskiqEpubAdapter
from app.presentation.api.depends import (
    book_protocol,
    ensure_gateway_request,
    get_check_admin,
)
from app.presentation.schemas.book.add_book_schemas import (
    AddBookRequestSchema,
    AddBookResponseSchema,
)
from app.presentation.schemas.book.admin_upload_schemas import (
    UploadInitRequestSchema,
    UploadJobListResponseSchema,
    UploadJobResponseSchema,
)
from app.presentation.schemas.book.get_book_schemas import (
    GetBookListResponse,
    GetBookResponseSchemas,
)
from app.presentation.schemas.book.update_book_schemas import (
    UpdateBookRequestSchema,
    UpdateBookResponseSchema,
)

logger = logging.getLogger(__name__)


book_router = APIRouter(tags=["books"], dependencies=[Depends(ensure_gateway_request)])


@book_router.post("/add", response_model=AddBookResponseSchema)
async def add_book(
    add_book_schema: AddBookRequestSchema,
    protocol=Depends(book_protocol),
    _: dict = Depends(get_check_admin),
):
    usecase = CreateBookUsecase(protocol)
    try:
        create_book = await usecase(add_book_schema)
        return create_book
    except Exception as error:
        logger.exception("Failed to add book")
        raise HTTPException(status_code=400, detail="Failed to add book")


@book_router.put("/update/{book_id}", response_model=UpdateBookResponseSchema)
async def update_book(
    book_id: int,
    update_book_schema: UpdateBookRequestSchema,
    protocol=Depends(book_protocol),
    _: dict = Depends(get_check_admin),
):
    usecase = UpdateBookUsecase(protocol)
    try:
        update_book_result = await usecase(
            book_id=book_id,
            title=update_book_schema.title,
            author=update_book_schema.author,
            description=update_book_schema.description,
            pic_url=update_book_schema.pic_url,
            difficulty=update_book_schema.difficulty,
        )
        return update_book_result
    except Exception as error:
        logger.exception("Failed to update book %s", book_id)
        raise HTTPException(status_code=400, detail="Failed to update book")


@book_router.get("/get/{book_id}", response_model=GetBookResponseSchemas)
async def get_book(
    book_id: int,
    protocol=Depends(book_protocol),
):
    usecase = GetBookUsecase(protocol)
    try:
        get_book_result = await usecase(book_id)
        return get_book_result
    except Exception as error:
        logger.exception("Failed to get book %s", book_id)
        raise HTTPException(status_code=400, detail="Failed to get book")


@book_router.delete("/delete", response_model=dict)
async def delete_book(
    book_id: int,
    protocol=Depends(book_protocol),
    _: dict = Depends(get_check_admin),
):
    usecase = DeleteBookUsecase(protocol)
    try:
        await usecase(book_id)
        return {"message": "Book deleted"}
    except Exception as error:
        logger.exception("Failed to delete book %s", book_id)
        raise HTTPException(status_code=400, detail="Failed to delete book")


@book_router.get("/list", response_model=GetBookListResponse)
async def list_book(
    limit: int = 20,
    cursor: Optional[str] = None,
    protocol=Depends(book_protocol),
):
    usecase = BookListUsecase(protocol)
    try:
        list_book_result = await usecase(limit, cursor)
        return list_book_result
    except Exception as error:
        logger.exception("Failed to list books")
        raise HTTPException(status_code=400, detail="Failed to list books")


@book_router.get("/find_by_title_author")
async def find_by_title_author(
    title: str,
    author: str,
    protocol=Depends(book_protocol),
):
    usecase = FindByTitleBookUsecase(protocol)
    try:
        find_by_title_author_result = await usecase(title, author)
        return find_by_title_author_result
    except Exception as error:
        logger.exception("Failed to search book by title and author")
        raise HTTPException(status_code=400, detail="Failed to search books")


@book_router.post(
    "/admin/uploads/init",
    response_model=UploadJobResponseSchema,
    status_code=201,
)
async def init_admin_upload(
    payload: UploadInitRequestSchema,
    admin: dict = Depends(get_check_admin),
    session: AsyncSession = Depends(get_session),
):
    usecase = InitBookUploadUsecase(BookUploadJobRepository(session))
    try:
        return await usecase(
            filename=payload.filename,
            difficulty=payload.difficulty,
            created_by_user_id=admin["x-user-id"],
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload init payload")
    except Exception:
        logger.exception("Failed to initialize admin upload")
        raise HTTPException(status_code=500, detail="Failed to initialize upload")


@book_router.post(
    "/admin/uploads/{upload_id}/complete",
    response_model=UploadJobResponseSchema,
)
async def complete_admin_upload(
    upload_id: str,
    file: UploadFile = File(...),
    admin: dict = Depends(get_check_admin),
    session: AsyncSession = Depends(get_session),
):
    usecase = CompleteBookUploadUsecase(
        job_repo=BookUploadJobRepository(session),
        storage=S3Storage(),
        processor=TaskiqEpubAdapter(),
    )
    try:
        return await usecase(
            upload_id=upload_id,
            file=file,
            requested_by_user_id=admin["x-user-id"],
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Upload job not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Upload job access denied")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload request")
    except Exception as error:
        logger.exception("Failed to complete admin upload %s", upload_id)
        raise HTTPException(status_code=500, detail="Failed to complete upload")


@book_router.get("/admin/uploads/{upload_id}", response_model=UploadJobResponseSchema)
async def get_upload_status(
    upload_id: str,
    _: dict = Depends(get_check_admin),
    session: AsyncSession = Depends(get_session),
):
    usecase = GetBookUploadUsecase(BookUploadJobRepository(session))
    try:
        return await usecase(upload_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Upload job not found")
    except Exception:
        logger.exception("Failed to get upload status for %s", upload_id)
        raise HTTPException(status_code=500, detail="Failed to get upload status")


@book_router.get("/admin/uploads", response_model=UploadJobListResponseSchema)
async def list_uploads(
    limit: int = 20,
    _: dict = Depends(get_check_admin),
    session: AsyncSession = Depends(get_session),
):
    usecase = ListBookUploadsUsecase(BookUploadJobRepository(session))
    return {"items": await usecase(limit=limit)}


@book_router.post("/admin/add-book")
async def admin_add_book(
    file: UploadFile = File(...),
    difficulty: int | None = Query(default=None, ge=1, le=6),
    admin: dict = Depends(get_check_admin),
    session: AsyncSession = Depends(get_session),
):
    init_usecase = InitBookUploadUsecase(BookUploadJobRepository(session))
    complete_usecase = CompleteBookUploadUsecase(
        job_repo=BookUploadJobRepository(session),
        storage=S3Storage(),
        processor=TaskiqEpubAdapter(),
    )
    try:
        created_job = await init_usecase(
            filename=file.filename or "uploaded.epub",
            difficulty=difficulty,
            created_by_user_id=admin["x-user-id"],
        )
        queued_job = await complete_usecase(
            upload_id=created_job.upload_id,
            file=file,
            requested_by_user_id=admin["x-user-id"],
        )
        return {
            "status": "success",
            "message": "Book accepted and queued for processing",
            "upload_id": queued_job.upload_id,
            "job_status": queued_job.status,
        }
    except LookupError:
        raise HTTPException(status_code=404, detail="Upload job not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Upload job access denied")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload payload")
    except Exception as error:
        logger.exception("Failed to handle admin add-book upload")
        raise HTTPException(status_code=500, detail="Failed to upload book")

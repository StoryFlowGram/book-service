import logging
from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
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
from app.application.service.cover_fallback_service import build_fallback_cover_svg
from app.infrastructure.database.session import get_session
from app.infrastructure.events.search_index_publisher import SearchIndexBookEventPublisher
from app.infrastructure.repositories.book_upload_job_repository import BookUploadJobRepository
from app.infrastructure.s3.s3_storage import S3Storage
from app.infrastructure.taskiq.taskiq_adapter import (
    TaskQueueUnavailableError,
    TaskiqEpubAdapter,
)
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
from app.presentation.api.depends import storage as storage_dep

logger = logging.getLogger(__name__)
search_index_event_publisher = SearchIndexBookEventPublisher()


book_router = APIRouter(tags=["books"], dependencies=[Depends(ensure_gateway_request)])
COVER_PROXY_PATH_TEMPLATE = "/api/v1/book/cover/{book_id}"
QUEUE_UNAVAILABLE_DETAIL = (
    "Черга обробки тимчасово недоступна. Перевірте RabbitMQ і TASKIQ_BROKER_URL."
)


async def _resolve_cover_url(storage: S3Storage, book_id: int, pic_url: str | None) -> str | None:
    if not pic_url:
        return COVER_PROXY_PATH_TEMPLATE.format(book_id=book_id)

    if getattr(storage, "bucket_public", False):
        try:
            return storage.build_public_object_url(pic_url)
        except Exception:
            logger.warning(
                "Failed to build public cover URL for book %s. Falling back to API proxy.",
                book_id,
            )
            return COVER_PROXY_PATH_TEMPLATE.format(book_id=book_id)

    # Private bucket mode: use presigned URL if browser-reachable endpoint is configured.
    if not getattr(storage, "public_endpoint_url", None):
        return COVER_PROXY_PATH_TEMPLATE.format(book_id=book_id)

    try:
        return await storage.generate_presigned_get_url(pic_url)
    except Exception:
        logger.warning(
            "Failed to generate presigned cover URL for book %s. Falling back to API proxy.",
            book_id,
        )
        return COVER_PROXY_PATH_TEMPLATE.format(book_id=book_id)


async def _attach_cover_url(storage: S3Storage, book_item):
    payload = asdict(book_item)
    payload["cover_url"] = await _resolve_cover_url(
        storage=storage,
        book_id=book_item.id,
        pic_url=book_item.pic_url,
    )
    return payload


async def _publish_search_event_safely(
    event_type: str,
    payload: dict | None = None,
    book_id: int | None = None,
):
    try:
        if event_type == "book.created" and payload:
            await search_index_event_publisher.publish_created(payload)
            return

        if event_type == "book.updated" and payload:
            await search_index_event_publisher.publish_updated(payload)
            return

        if event_type == "book.deleted" and book_id is not None:
            await search_index_event_publisher.publish_deleted(book_id)
            return

        logger.warning(
            "Unsupported search event publishing request. event_type=%s has_payload=%s book_id=%s",
            event_type,
            payload is not None,
            book_id,
        )
    except Exception:
        logger.exception(
            "Failed to publish search index event. event_type=%s book_id=%s",
            event_type,
            book_id or (payload or {}).get("id"),
        )


@book_router.post("/add", response_model=AddBookResponseSchema)
async def add_book(
    add_book_schema: AddBookRequestSchema,
    protocol=Depends(book_protocol),
    storage = Depends(storage_dep, use_cache=True),
    _: dict = Depends(get_check_admin),
):
    usecase = CreateBookUsecase(protocol)
    try:
        create_book = await usecase(add_book_schema)
        response_payload = await _attach_cover_url(storage, create_book)
        await _publish_search_event_safely(event_type="book.created", payload=response_payload)
        return response_payload
    except Exception:
        logger.exception("Ошибка добавления книги")
        raise HTTPException(status_code=400, detail="Не вдалося додати книгу")


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
        storage = S3Storage()
        response_payload = await _attach_cover_url(storage, update_book_result)
        await _publish_search_event_safely(event_type="book.updated", payload=response_payload)
        return response_payload
    except Exception:
        logger.exception("Failed to update book %s", book_id)
        raise HTTPException(status_code=400, detail="Не вдалося оновити книгу")


@book_router.get("/get/{book_id}", response_model=GetBookResponseSchemas)
async def get_book(
    book_id: int,
    protocol=Depends(book_protocol),
):
    usecase = GetBookUsecase(protocol)
    try:
        get_book_result = await usecase(book_id)
        storage = S3Storage()
        return await _attach_cover_url(storage, get_book_result)
    except Exception:
        logger.exception("Failed to get book %s", book_id)
        raise HTTPException(status_code=400, detail="Не вдалося отримати книгу")


@book_router.get("/cover/{book_id}/presigned", response_model=dict)
async def get_book_cover_presigned_url(
    book_id: int,
    protocol=Depends(book_protocol),
):
    try:
        book = await protocol.get(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Cover not found")

        if not book.pic_url:
            return {"cover_url": COVER_PROXY_PATH_TEMPLATE.format(book_id=book_id)}

        storage = S3Storage()
        cover_url = await _resolve_cover_url(storage, book_id=book_id, pic_url=book.pic_url)
        return {"cover_url": cover_url}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to generate presigned cover URL for book %s", book_id)
        raise HTTPException(status_code=500, detail="Failed to generate cover URL")


@book_router.get("/cover/{book_id}")
async def get_book_cover(
    book_id: int,
    protocol=Depends(book_protocol),
):
    book = None
    try:
        book = await protocol.get(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Обкладинку не знайдено")

        if not book.pic_url:
            fallback_cover = build_fallback_cover_svg(book.title, book.author)
            return Response(
                content=fallback_cover,
                media_type="image/svg+xml",
                headers={"Cache-Control": "public, max-age=86400"},
            )

        storage = S3Storage()
        cover_bytes, content_type = await storage.get_object_bytes(book.pic_url)
        if not (content_type or "").startswith("image/"):
            logger.warning(
                "Cover for book %s has non-image content type '%s'. Serving fallback.",
                book_id,
                content_type,
            )
            fallback_cover = build_fallback_cover_svg(book.title, book.author)
            return Response(
                content=fallback_cover,
                media_type="image/svg+xml",
                headers={"Cache-Control": "public, max-age=300"},
            )

        return Response(
            content=cover_bytes,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except HTTPException:
        raise
    except ValueError:
        fallback_cover = build_fallback_cover_svg(
            getattr(book, "title", "Untitled"),
            getattr(book, "author", "Unknown Author"),
        )
        return Response(
            content=fallback_cover,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception:
        logger.exception("Failed to load cover for book %s", book_id)
        fallback_cover = build_fallback_cover_svg(
            getattr(book, "title", "Untitled"),
            getattr(book, "author", "Unknown Author"),
        )
        return Response(
            content=fallback_cover,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=300"},
        )


@book_router.delete("/delete", response_model=dict)
async def delete_book(
    book_id: int,
    protocol=Depends(book_protocol),
    _: dict = Depends(get_check_admin),
):
    usecase = DeleteBookUsecase(protocol)
    try:
        await usecase(book_id)
        await _publish_search_event_safely(event_type="book.deleted", book_id=book_id)
        return {"message": "Книгу видалено"}
    except Exception:
        logger.exception("Failed to delete book %s", book_id)
        raise HTTPException(status_code=400, detail="Не вдалося видалити книгу")


@book_router.get("/list", response_model=GetBookListResponse)
async def list_book(
    limit: int = 20,
    cursor: Optional[str] = None,
    protocol=Depends(book_protocol),
):
    usecase = BookListUsecase(protocol)
    try:
        list_book_result = await usecase(limit, cursor)
        storage = S3Storage()
        items = [
            await _attach_cover_url(storage, book_item)
            for book_item in list_book_result["items"]
        ]
        return {
            "items": items,
            "next_cursor": list_book_result["next_cursor"],
        }
    except Exception:
        logger.exception("Failed to list books")
        raise HTTPException(status_code=400, detail="Не вдалося отримати список книг")


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
    except Exception:
        logger.exception("Failed to search book by title and author")
        raise HTTPException(status_code=400, detail="Не вдалося виконати пошук книг")


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
        raise HTTPException(status_code=400, detail="Некоректні дані для ініціалізації завантаження")
    except Exception:
        logger.exception("Failed to initialize admin upload")
        raise HTTPException(status_code=500, detail="Не вдалося ініціалізувати завантаження")


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
        raise HTTPException(status_code=404, detail="Задачу завантаження не знайдено")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Немає доступу до задачі завантаження")
    except ValueError:
        raise HTTPException(status_code=400, detail="Некоректні дані завантаження")
    except TaskQueueUnavailableError:
        raise HTTPException(
            status_code=503,
            detail=QUEUE_UNAVAILABLE_DETAIL,
        )
    except Exception:
        logger.exception("Failed to complete admin upload %s", upload_id)
        raise HTTPException(status_code=500, detail="Не вдалося завершити завантаження")


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
        raise HTTPException(status_code=404, detail="Задачу завантаження не знайдено")
    except Exception:
        logger.exception("Failed to get upload status for %s", upload_id)
        raise HTTPException(status_code=500, detail="Не вдалося отримати статус завантаження")


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
            "message": "Книгу прийнято та поставлено в чергу на обробку",
            "upload_id": queued_job.upload_id,
            "job_status": queued_job.status,
        }
    except LookupError:
        raise HTTPException(status_code=404, detail="Задачу завантаження не знайдено")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Немає доступу до задачі завантаження")
    except ValueError:
        raise HTTPException(status_code=400, detail="Некоректні дані завантаження")
    except TaskQueueUnavailableError:
        raise HTTPException(
            status_code=503,
            detail=QUEUE_UNAVAILABLE_DETAIL,
        )
    except Exception:
        logger.exception("Failed to handle admin add-book upload")
        raise HTTPException(status_code=500, detail="Не вдалося завантажити книгу")

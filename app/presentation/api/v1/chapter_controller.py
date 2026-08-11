import logging

from fastapi import APIRouter, Depends, HTTPException

from app.application.usecase.chapter.add_chapter import AddChapterUsecase
from app.application.usecase.chapter.delete_chapter import DeleteChapterUsecase
from app.application.usecase.chapter.get_chapter_content import GetChapterContentUsecase
from app.application.usecase.chapter.get_chapters_by_book_id import GetChapterByIdUsecase
from app.presentation.api.depends import (
    book_protocol,
    chapter_protocol,
    ensure_gateway_request,
    get_check_admin,
    storage,
)
from app.presentation.schemas.chapter.add_chapter_schemas import (
    AddChapterRequestSchema,
    AddChapterResponseSchema,
)

logger = logging.getLogger(__name__)

chapter_router = APIRouter(tags=["chapters"], dependencies=[Depends(ensure_gateway_request)])


@chapter_router.post("/add", response_model=AddChapterResponseSchema)
async def add_chapter(
    add_chapter_schema: AddChapterRequestSchema,
    chapter_protocol=Depends(chapter_protocol),
    book_protocol=Depends(book_protocol),
    _: dict = Depends(get_check_admin),
):
    usecase = AddChapterUsecase(chapter_protocol, book_protocol)
    try:
        return await usecase(add_chapter_schema)
    except Exception:
        logger.exception("Failed to add chapter")
        raise HTTPException(status_code=400, detail="Не вдалося додати розділ")


@chapter_router.get("/{book_id}/chapters")
async def get_chapters_list(book_id: int, protocol=Depends(chapter_protocol)):
    usecase = GetChapterByIdUsecase(protocol)
    try:
        return await usecase(book_id)
    except Exception:
        logger.exception("Failed to get chapter list for book %s", book_id)
        raise HTTPException(status_code=400, detail="Не вдалося отримати список розділів")


@chapter_router.get("/chapter/{chapter_id}/content")
async def get_chapter_content(
    chapter_id: int,
    chapter_protocol=Depends(chapter_protocol),
    storage=Depends(storage),
):
    usecase = GetChapterContentUsecase(chapter_repository=chapter_protocol, storage=storage)
    try:
        content = await usecase(chapter_id)
        return {"content": content}
    except ValueError:
        raise HTTPException(status_code=404, detail="Текст розділу не знайдено")
    except Exception:
        logger.exception("Failed to get chapter content for chapter %s", chapter_id)
        raise HTTPException(status_code=400, detail="Не вдалося отримати текст розділу")


@chapter_router.delete("/delete", response_model=dict)
async def delete_chapter(
    chapter_id: int,
    protocol=Depends(chapter_protocol),
    _: dict = Depends(get_check_admin),
):
    usecase = DeleteChapterUsecase(protocol)
    try:
        await usecase(chapter_id)
        return {"message": "Розділ успішно видалено"}
    except Exception:
        logger.exception("Failed to delete chapter %s", chapter_id)
        raise HTTPException(status_code=400, detail="Не вдалося видалити розділ")

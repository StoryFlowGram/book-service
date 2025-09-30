from fastapi import APIRouter, Depends, HTTPException

from app.application.usecase.chapter.add_chapter import AddChapterUsecase
from app.application.usecase.chapter.delete_chapter import DeleteChapterUsecase
from app.application.usecase.chapter.get_chapter_by_id import GetChapterByIdUsecase
from app.application.usecase.chapter.get_chapter_content import GetChapterContent


from app.presentation.schemas.chapter.add_chapter_schemas import AddChapterResponseSchema, AddChapterRequestSchema
from app.presentation.schemas.chapter.get_chapter_schemas import GetChapterResponseSchemas

from app.presentation.api.depends import chapter_protocol, get_current_user, book_protocol, storage

chapter_router = APIRouter(
    prefix="/api/v1/chapters",
    tags=["chapters"],
)


@chapter_router.post("/add", response_model=AddChapterResponseSchema)
async def add_chapter(
    add_chapter_schema: AddChapterRequestSchema,
    chapter_protocol = Depends(chapter_protocol),
    book_protocol = Depends(book_protocol),
    get_current_user = Depends(get_current_user),
):
    usecase = AddChapterUsecase(chapter_protocol, book_protocol)
    try:
        add_chapter = await usecase(add_chapter_schema)
        return add_chapter
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@chapter_router.get("/get/{chapter_id}", response_model=GetChapterResponseSchemas)
async def get_chapter(
    chapter_id: int,
    protocol = Depends(chapter_protocol),
    get_current_user = Depends(get_current_user),
):
    usecase = GetChapterByIdUsecase(protocol)
    try:
        get_chapter = await usecase(chapter_id)
        return get_chapter
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@chapter_router.delete("/delete", response_model=dict)
async def delete_chapter(
    chapter_id: int,
    protocol = Depends(chapter_protocol),
    get_current_user = Depends(get_current_user)
):
    usecase = DeleteChapterUsecase(protocol)
    try:
        await usecase(chapter_id)
        return {"message": "Глава успешно удалена"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@chapter_router.get("/chapter/{chapter_id}")
async def get_chapter_content(
    chapter_id: int,
    chapter_protocol = Depends(chapter_protocol),
    storage = Depends(storage)
):
    usecase = GetChapterContent(chapter_repository=chapter_protocol, storage=storage)
    try:
        content = await usecase(chapter_id)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
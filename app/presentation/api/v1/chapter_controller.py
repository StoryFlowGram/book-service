from fastapi import APIRouter, Depends, HTTPException

from app.application.usecase.chapter.add_chapter import AddChapterUsecase
from app.application.usecase.chapter.delete_chapter import DeleteChapterUsecase
from app.application.usecase.chapter.get_chapters_by_book_id import GetChapterByIdUsecase
from app.application.usecase.chapter.get_chapter_content import GetChapterContentUsecase


from app.presentation.schemas.chapter.add_chapter_schemas import AddChapterResponseSchema, AddChapterRequestSchema

from app.presentation.api.depends import chapter_protocol,  book_protocol, storage

chapter_router = APIRouter(tags=["chapters"])


@chapter_router.post("/add", response_model=AddChapterResponseSchema)
async def add_chapter(
    add_chapter_schema: AddChapterRequestSchema,
    chapter_protocol = Depends(chapter_protocol),
    book_protocol = Depends(book_protocol)
):
    usecase = AddChapterUsecase(chapter_protocol, book_protocol)
    try:
        add_chapter = await usecase(add_chapter_schema)
        return add_chapter
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@chapter_router.get("/{book_id}/chapters") 
async def get_chapters_list(book_id: int,protocol = Depends(chapter_protocol)):
    usecase = GetChapterByIdUsecase(protocol)
    try:
        get_chapter = await usecase(book_id)
        return get_chapter
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@chapter_router.get("/chapter/{chapter_id}/content")
async def get_chapter_content(
    chapter_id: int,
    chapter_protocol = Depends(chapter_protocol),
    storage = Depends(storage)
):
    usecase = GetChapterContentUsecase(chapter_repository=chapter_protocol, storage=storage)
    try:
        content = await usecase(chapter_id)
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@chapter_router.delete("/delete", response_model=dict)
async def delete_chapter(
    chapter_id: int,
    protocol = Depends(chapter_protocol)
):
    usecase = DeleteChapterUsecase(protocol)
    try:
        await usecase(chapter_id)
        return {"message": "Глава успешно удалена"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
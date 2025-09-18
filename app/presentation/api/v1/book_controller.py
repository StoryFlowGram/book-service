from typing import Optional
from fastapi import APIRouter, HTTPException, Depends

from app.application.usecase.book.create_book import CreateBookUsecase
from app.application.usecase.book.update_book import UpdateBookUsecase
from app.application.usecase.book.get_book import GetBookUsecase
from app.application.usecase.book.delete_book import DeleteBookUsecase
from app.application.usecase.book.list_book import BookListUsecase
from app.application.usecase.book.find_by_title_book import FindByTitleBookUsecase

from app.presentation.schemas.book.add_book_schemas import AddBookResponseSchema, AddBookRequestSchema
from app.presentation.schemas.book.update_book_schemas import UpdateBookRequestSchema, UpdateBookResponseSchema
from app.presentation.schemas.book.get_book_schemas import GetBookResponseSchemas

from app.presentation.api.depends import book_protocol, token_verifier, get_current_user


book_router = APIRouter(
    prefix="/api/v1/books",
    tags=["books"],
)

@book_router.post("/add", response_model=AddBookResponseSchema)
async def add_book(
    add_book_schema: AddBookRequestSchema,
    protocol = Depends(book_protocol),
    get_current_user_jwt = Depends(get_current_user),
):
    usecase = CreateBookUsecase(protocol)
    try:
        create_book = await usecase(add_book_schema)
        return create_book
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@book_router.put("/update/{book_id}", response_model=UpdateBookResponseSchema)
async def update_book(
    book_id: int,
    update_book_schema: UpdateBookRequestSchema,
    protocol = Depends(book_protocol),
    get_current_user_jwt = Depends(get_current_user),
):
    usecase = UpdateBookUsecase(protocol)
    try:
        update_book = await usecase(book_id=book_id, title=update_book_schema.title, author=update_book_schema.author, description=update_book_schema.description, pic_url=update_book_schema.pic_url, difficulty=update_book_schema.difficulty)
        return update_book
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@book_router.get("/get/{book_id}", response_model=GetBookResponseSchemas)
async def get_book(
    book_id: int,
    protocol = Depends(book_protocol),
    get_current_user_jwt = Depends(get_current_user),
):
    usecase = GetBookUsecase(protocol)
    try:
        get_book = await usecase(book_id)
        return get_book
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@book_router.delete("/delete", response_model=dict)
async def delete_book(
    book_id: int,
    protocol = Depends(book_protocol),
    get_current_user = Depends(get_current_user)
):
    usecase = DeleteBookUsecase(protocol)
    try:
        await usecase(book_id)
        return {"message": "Книга удалена"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail = str(e))
    
@book_router.get("/list", response_model=list)
async def list_book(
    limit: int = 20,
    cursor: Optional[str] = None,
    protocol = Depends(book_protocol),
    get_current_user = Depends(get_current_user)
):
    usecase = BookListUsecase(protocol)
    try:
        list_book = await usecase(limit, cursor)
        return list_book
    except Exception as e:
        raise HTTPException(status_code=400, detail = str(e))
    
@book_router.get("/find_by_title_author")
async def find_by_title_author(
    title: str,
    author: str,
    protocol = Depends(book_protocol),
    get_current_user = Depends(get_current_user)
):
    usecase = FindByTitleBookUsecase(protocol)
    try:
        find_by_title_author = await usecase(title, author)
        return find_by_title_author
    except Exception as e:
        raise HTTPException(status_code=400, detail = str(e))
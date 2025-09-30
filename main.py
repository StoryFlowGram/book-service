# main.py
from fastapi import FastAPI
from app.presentation.api.v1.book_controller import book_router
from app.presentation.api.v1.chapter_controller import chapter_router
from app.presentation.api import depends
from app.infrastructure import di
from app.infrastructure.models.book_model import Book
from app.infrastructure.models.chapter_model import Chapter
from app.infrastructure.database.base import Base
from app.infrastructure.database.engine import engine
from app.infrastructure.taskiq.broker import broker  

app = FastAPI(title="Book And Chapter Service")

app.include_router(book_router)
app.include_router(chapter_router)

app.dependency_overrides[depends.book_protocol] = di.book_protocol
app.dependency_overrides[depends.token_verifier] = di.token_verifier
app.dependency_overrides[depends.chapter_protocol] = di.chapter_protocol
app.dependency_overrides[depends.storage] = di.storage

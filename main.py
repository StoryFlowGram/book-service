from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.database.base import Base
from app.infrastructure.database.engine import engine
from app.infrastructure.models.book_model import Book
from app.infrastructure.models.chapter_model import Chapter
from app.infrastructure.taskiq.broker import broker, startup_broker_with_retry
from app.presentation.api import depends
from app.presentation.api.v1.book_controller import book_router
from app.presentation.api.v1.chapter_controller import chapter_router
from app.infrastructure import di


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_broker_with_retry()
    yield
    await broker.shutdown()


app = FastAPI(title="Book And Chapter Service", lifespan=lifespan)

app.include_router(book_router)
app.include_router(chapter_router)

app.dependency_overrides[depends.book_protocol] = di.book_protocol
app.dependency_overrides[depends.chapter_protocol] = di.chapter_protocol
app.dependency_overrides[depends.storage] = di.storage


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "book-service"}

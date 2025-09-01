from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.infrastructure.database.engine import  engine


session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with session_factory() as session:
        yield session
from app.infrastructure.config.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

config = Config(env_file=".env")

engine = create_async_engine(
    url=config.db.get_database_url(),
    echo=config.app.DEBUG,
)
from pydantic_settings import BaseSettings
from sqlalchemy import URL


class DatabaseConfig(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str

    def get_database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            database=self.DB_NAME,
        )

    model_config = {
        "extra": "ignore",
        "env_file_encoding": "utf-8",
    }


class AppConfig(BaseSettings):
    DEBUG: bool = True
    ENVIRONMENT: str = "production" 
    SECRET_KEY: str = "dev-secret" 

    model_config = {
        "extra": "ignore",
        "env_file_encoding": "utf-8",
    }


class JWTConfig(BaseSettings):
    JWT_ALGORITHM: str
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int =  14

    model_config = {
        "extra": "ignore",
        "env_file_encoding": "utf-8",
    }

class Config:
    def __init__(self, env_file: str | None = None):
        self.app = AppConfig(_env_file=env_file)
        self.jwt = JWTConfig(_env_file=env_file)
        self.db = DatabaseConfig(_env_file=env_file)

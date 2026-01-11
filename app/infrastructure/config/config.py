from pydantic_settings import BaseSettings
from sqlalchemy import URL


class DatabaseConfig(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_NAME: str

    def get_database_url(self, DB_API: str) -> URL:
        return URL.create(
            drivername=f"postgresql+{DB_API}",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_DB,
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



class S3Config(BaseSettings):
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    S3_REGION_NAME: str
    S3_BUCKET_NAME: str 
    S3_ENDPOINT_URL: str


    model_config = {
        "extra": "ignore",
        "env_file_encoding": "utf-8",
    }

class TaskiqConfig(BaseSettings):
    TASKIQ_BROKER_URL: str

    model_config = {
        "extra": "ignore",
        "env_file_encoding": "utf-8",
    }


class Config:
    def __init__(self, env_file: str | None = None):
        self.app = AppConfig(_env_file=env_file)
        self.db = DatabaseConfig(_env_file=env_file)
        self.taskiq = TaskiqConfig(_env_file=env_file)
        self.s3 = S3Config(_env_file=env_file)

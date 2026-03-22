from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    user: str = Field(alias="BOOK_DB_USER")
    password: str = Field(alias="BOOK_DB_PASSWORD")
    db_name: str = Field(alias="BOOK_DB_NAME")
    
    host: str = Field(default="book-db", alias="BOOK_DB_HOST")
    port: int = 5432

    def get_database_url(self, DB_API: str) -> URL:
        return URL.create(
            drivername=f"postgresql+{DB_API}",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.db_name,
        )

class S3Config(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    minio_root_user: str = Field(alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(alias="MINIO_ROOT_PASSWORD")
    s3_region_name: str = Field(alias="S3_REGION_NAME")
    s3_bucket_name: str = Field(alias="S3_BUCKET_NAME")
    s3_endpoint_url: str = Field(alias="S3_ENDPOINT_URL")

class TaskiqConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    taskiq_broker_url: str = Field(alias="TASKIQ_BROKER_URL")

class Config:
    def __init__(self):
        self.db = DatabaseConfig()
        self.taskiq = TaskiqConfig()
        self.s3 = S3Config()
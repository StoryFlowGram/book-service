from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

class DatabaseConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    user: str = Field(alias="BOOK_DB_USER")
    password: str = Field(alias="BOOK_DB_PASSWORD")
    db_name: str = Field(alias="BOOK_DB_NAME")
    
    host: str = Field(alias="BOOK_DB_HOST")
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
    s3_bucket_public: bool = Field(default=False, alias="S3_BUCKET_PUBLIC")
    s3_presigned_expires_seconds: int = Field(default=900, alias="S3_PRESIGNED_EXPIRES_SECONDS")
    s3_public_endpoint_url: str | None = Field(default=None, alias="S3_PUBLIC_ENDPOINT_URL")

class TaskiqConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    taskiq_broker_url: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        alias="TASKIQ_BROKER_URL",
    )
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@rabbitmq:5672/",
        alias="RABBITMQ_URL",
    )
    startup_connect_retries: int = Field(default=20, alias="TASKIQ_STARTUP_CONNECT_RETRIES")
    startup_connect_delay_seconds: float = Field(
        default=2.0,
        alias="TASKIQ_STARTUP_CONNECT_DELAY_SECONDS",
    )

    @model_validator(mode="after")
    def normalize_broker_url(self):
        raw_value = (self.taskiq_broker_url or "").strip()

        if raw_value.startswith(("redis://", "rediss://")):
            fallback = (self.rabbitmq_url or "").strip()
            self.taskiq_broker_url = fallback or "amqp://guest:guest@rabbitmq:5672/"
            return self

        if not raw_value.startswith(("amqp://", "amqps://")):
            raise ValueError("TASKIQ_BROKER_URL must use AMQP (amqp:// or amqps://) for RabbitMQ")

        self.taskiq_broker_url = raw_value
        return self

class Config:
    def __init__(self):
        self.db = DatabaseConfig()
        self.taskiq = TaskiqConfig()
        self.s3 = S3Config()
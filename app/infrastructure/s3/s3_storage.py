import aioboto3
from app.infrastructure.config.config import Config
import logging
import tempfile
import httpx

from app.application.interfaces.storage import AbstractStorage

config = Config(".env")
logger = logging.getLogger(__name__)

class S3Storage(AbstractStorage):
    def __init__(self):
        self.endpoint_url = config.s3.S3_ENDPOINT_URL
        self.bucket_name = config.s3.S3_BUCKET_NAME
        self.aws_access_key_id = config.s3.MINIO_ROOT_USER
        self.aws_secret_access_key = config.s3.MINIO_ROOT_PASSWORD
        self.region_name = config.s3.S3_REGION_NAME
        self.session = aioboto3.Session()

    async def _ensure_bucket_exists(self):
        try:
            logger.info(f"Проверяю бакет '{self.bucket_name}'...")
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            ) as s3:
                await s3.head_bucket(Bucket=self.bucket_name)
                logger.info(f"Бакет '{self.bucket_name}' уже существует.")
        except Exception as e:
            if hasattr(e, 'response') and e.response.get('Error', {}).get('Code') == '404':
                try:
                    logger.info(f"Создаю бакет '{self.bucket_name}'...")
                    async with self.session.client(
                        's3',
                        endpoint_url=self.endpoint_url,
                        aws_access_key_id=self.aws_access_key_id,
                        aws_secret_access_key=self.aws_secret_access_key,
                        region_name=self.region_name
                    ) as s3:
                        await s3.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Бакет '{self.bucket_name}' создан автоматически.")
                except Exception as create_e:
                    logger.error(f"Ошибка создания бакета: {create_e}")
                    raise
            else:
                logger.error(f"Ошибка проверки бакета: {e}")
                raise

    async def upload_fileobj(self, fileobj, object_name: str) -> str:
        await self._ensure_bucket_exists()
        try:
            logger.info(f"Загружаю {object_name} в бакет '{self.bucket_name}'...")
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            ) as s3:
                await s3.upload_fileobj(fileobj, self.bucket_name, object_name)
            logger.info(f"Uploaded {object_name} to S3")
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
        except Exception as e:
            logger.error(f"Error uploading fileobj to S3: {e}")
            raise

    async def download_to_temp(self, object_name: str) -> str:
        await self._ensure_bucket_exists()
        try:
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            ) as s3:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
                    await s3.download_fileobj(self.bucket_name, object_name, tmp)
                    logger.info(f"Скачан {object_name} в {tmp.name}")
                    return tmp.name
        except Exception as e:
            logger.error(f"Ошибка скачивания {object_name}: {e}")
            raise

    async def delete_object(self, object_name: str):
        await self._ensure_bucket_exists()
        try:
            logger.info(f"Удаляю {object_name} из бакета '{self.bucket_name}'...")
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            ) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"Deleted {object_name} from S3")
        except Exception as e:
            logger.warning(f"Error deleting {object_name}: {e}")

    async def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        await self._ensure_bucket_exists()
        try:
            logger.info(f"Загружаю {object_name} (bytes) в бакет '{self.bucket_name}'...")
            async with self.session.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name, 
                    Key=object_name, 
                    Body=data, 
                    ContentType=content_type
                )
            logger.info(f"Uploaded {object_name} to S3")
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise

    async def upload_chapter_text(self, book_id: int, chapter_order: int, text: str) -> str:
        object_name = f"books/{book_id}/chapters/chapter_{chapter_order}.txt"
        return await self.upload_bytes(text.encode('utf-8'), object_name, content_type='text/plain')

    async def upload_cover(self, book_title: str, cover_data: bytes) -> str:
        object_name = f"books/covers/{book_title.replace(' ', '_')}.jpg"
        return await self.upload_bytes(cover_data, object_name, content_type='image/jpeg')
    
    async def get_object_content(self, s3_url: str) -> str:
        parsed_url = httpx.URL(s3_url)
        path_parts = parsed_url.path.strip('/').split('/', 1)
        if len(path_parts) != 2:
            raise ValueError("Некорректный S3 URL")
        bucket, key = path_parts

        async with self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        ) as s3:
            try:
                response = await s3.get_object(Bucket=bucket, Key=key)
                content = await response['Body'].read()
                return content.decode('utf-8', errors='ignore')
            except Exception as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    raise ValueError("Файл не найден в MinIO")
                raise e
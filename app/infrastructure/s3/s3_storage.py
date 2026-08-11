import inspect
import logging
import tempfile
from pathlib import PurePosixPath
from urllib.parse import quote
from uuid import uuid4

import aioboto3
import httpx

from app.application.interfaces.storage import AbstractStorage
from app.infrastructure.config.config import Config

config = Config()
logger = logging.getLogger(__name__)


class S3Storage(AbstractStorage):
    def __init__(self):
        self.endpoint_url = config.s3.s3_endpoint_url.rstrip("/")
        self.public_endpoint_url = (
            config.s3.s3_public_endpoint_url.rstrip("/")
            if config.s3.s3_public_endpoint_url
            else None
        )
        self.bucket_public = config.s3.s3_bucket_public
        self.presigned_expires_seconds = config.s3.s3_presigned_expires_seconds
        self.bucket_name = config.s3.s3_bucket_name
        self.aws_access_key_id = config.s3.minio_root_user
        self.aws_secret_access_key = config.s3.minio_root_password
        self.region_name = config.s3.s3_region_name
        self.session = aioboto3.Session()

    async def _ensure_bucket_exists(self):
        try:
            logger.info("Checking bucket '%s'", self.bucket_name)
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            ) as s3:
                await s3.head_bucket(Bucket=self.bucket_name)
        except Exception as error:
            code = getattr(error, "response", {}).get("Error", {}).get("Code")
            if code in {"404", "NoSuchBucket", "NotFound"}:
                logger.info("Creating bucket '%s'", self.bucket_name)
                async with self.session.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    region_name=self.region_name,
                ) as s3:
                    await s3.create_bucket(Bucket=self.bucket_name)
                return
            logger.error("Failed to check bucket '%s': %s", self.bucket_name, error)
            raise

    async def upload_fileobj(self, fileobj, object_name: str) -> str:
        await self._ensure_bucket_exists()
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            ) as s3:
                await s3.upload_fileobj(fileobj, self.bucket_name, object_name)
            logger.info("Uploaded %s to bucket %s", object_name, self.bucket_name)
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
        except Exception as error:
            logger.error("Failed to upload %s: %s", object_name, error)
            raise

    async def download_to_temp(self, object_name: str) -> str:
        await self._ensure_bucket_exists()
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            ) as s3:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp:
                    await s3.download_fileobj(self.bucket_name, object_name, tmp)
                    logger.info("Downloaded %s to %s", object_name, tmp.name)
                    return tmp.name
        except Exception as error:
            logger.error("Failed to download %s: %s", object_name, error)
            raise

    async def delete_object(self, object_name: str):
        await self._ensure_bucket_exists()
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            ) as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info("Deleted %s from bucket %s", object_name, self.bucket_name)
        except Exception as error:
            logger.warning("Failed to delete %s: %s", object_name, error)

    async def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        await self._ensure_bucket_exists()
        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            ) as s3:
                await s3.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=data,
                    ContentType=content_type,
                )
            logger.info("Uploaded bytes object %s to bucket %s", object_name, self.bucket_name)
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
        except Exception as error:
            logger.error("Failed to upload bytes for %s: %s", object_name, error)
            raise

    async def upload_chapter_text(self, book_id: int, chapter_order: int, text: str) -> str:
        object_name = f"books/{book_id}/chapters/chapter_{chapter_order}.html"
        return await self.upload_bytes(
            text.encode("utf-8"),
            object_name,
            content_type="text/html",
        )

    async def upload_cover(
        self,
        book_title: str,
        cover_data: bytes,
        content_type: str | None = None,
        source_file_name: str | None = None,
    ) -> str:
        normalized_type = self._resolve_cover_content_type(
            cover_data=cover_data,
            content_type=content_type,
            source_file_name=source_file_name,
        )
        extension_by_type = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
            "image/svg+xml": "svg",
            "image/bmp": "bmp",
        }
        extension = extension_by_type.get(normalized_type)
        if not extension and normalized_type.startswith("image/"):
            extension = normalized_type.split("/", 1)[1].split("+", 1)[0]
            if extension == "jpeg":
                extension = "jpg"
        extension = extension or "bin"
        safe_title = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in book_title).strip("_")
        safe_title = safe_title or "book_cover"
        unique_suffix = uuid4().hex[:12]
        object_name = f"books/covers/{safe_title}_{unique_suffix}.{extension}"
        return await self.upload_bytes(
            cover_data,
            object_name,
            content_type=normalized_type,
        )

    def _resolve_cover_content_type(
        self,
        cover_data: bytes,
        content_type: str | None,
        source_file_name: str | None,
    ) -> str:
        normalized = (content_type or "").strip().lower()
        if normalized in {"image/jpg", "image/pjpeg"}:
            normalized = "image/jpeg"

        if normalized.startswith("image/") and normalized != "application/octet-stream":
            return normalized

        detected_by_bytes = self._detect_image_content_type_from_bytes(cover_data)
        if detected_by_bytes:
            return detected_by_bytes

        detected_by_extension = self._detect_image_content_type_from_extension(source_file_name)
        if detected_by_extension:
            return detected_by_extension

        return "application/octet-stream"

    def _detect_image_content_type_from_extension(self, source_file_name: str | None) -> str | None:
        if not source_file_name:
            return None

        suffix = PurePosixPath(source_file_name).suffix.lower()
        ext_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".bmp": "image/bmp",
        }
        return ext_map.get(suffix)

    def _detect_image_content_type_from_bytes(self, data: bytes) -> str | None:
        if not data:
            return None

        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if data.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if data.startswith(b"BM"):
            return "image/bmp"
        if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
            return "image/webp"

        sample = data[:512].lstrip()
        lower_sample = sample.lower()
        if lower_sample.startswith(b"<?xml") and b"<svg" in lower_sample:
            return "image/svg+xml"
        if lower_sample.startswith(b"<svg") or b"<svg " in lower_sample:
            return "image/svg+xml"

        return None

    def _parse_bucket_and_key(self, s3_url: str) -> tuple[str, str]:
        parsed_url = httpx.URL(s3_url)
        path_parts = parsed_url.path.strip("/").split("/", 1)
        if len(path_parts) != 2:
            raise ValueError("Invalid S3 URL")
        return path_parts[0], path_parts[1]

    def build_public_object_url(self, s3_url: str) -> str:
        base_url = self.public_endpoint_url or self.endpoint_url
        bucket, key = self._parse_bucket_and_key(s3_url)
        quoted_key = quote(key, safe="/")
        return f"{base_url}/{bucket}/{quoted_key}"

    async def generate_presigned_get_url(self, s3_url: str, expires_seconds: int | None = None) -> str:
        bucket, key = self._parse_bucket_and_key(s3_url)
        ttl = expires_seconds or self.presigned_expires_seconds
        signing_endpoint_url = self.public_endpoint_url or self.endpoint_url

        async with self.session.client(
            "s3",
            endpoint_url=signing_endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        ) as s3:
            maybe_coroutine = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=ttl,
            )
            signed_url = (
                await maybe_coroutine
                if inspect.isawaitable(maybe_coroutine)
                else maybe_coroutine
            )

        return signed_url

    async def get_object_bytes(self, s3_url: str) -> tuple[bytes, str]:
        bucket, key = self._parse_bucket_and_key(s3_url)

        async with self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        ) as s3:
            try:
                response = await s3.get_object(Bucket=bucket, Key=key)
                content = await response["Body"].read()
                content_type = response.get("ContentType") or "application/octet-stream"
                if content_type == "application/octet-stream":
                    detected_type = self._detect_image_content_type_from_bytes(content)
                    if detected_type:
                        content_type = detected_type
                return content, content_type
            except Exception as error:
                if getattr(error, "response", {}).get("Error", {}).get("Code") == "NoSuchKey":
                    raise ValueError("File not found in MinIO")
                raise

    async def get_object_content(self, s3_url: str) -> str:
        content, _ = await self.get_object_bytes(s3_url)
        return content.decode("utf-8", errors="ignore")

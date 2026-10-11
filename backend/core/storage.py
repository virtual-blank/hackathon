from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aioboto3
from aiobotocore.client import AioBaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from core.config import get_minio_settings

# MinIO регион не использует, но без него клиент не подпишет запрос.
REGION = "us-east-1"
BUCKET_EXISTS_CODE = "BucketAlreadyOwnedByYou"
NOT_FOUND_CODE = "404"
CONNECT_TIMEOUT_SEC = 3

# ClientError — хранилище ответило отказом, BotoCoreError — до него не достучались.
STORAGE_ERRORS = (ClientError, BotoCoreError)

session = aioboto3.Session()


@asynccontextmanager
async def s3_client() -> AsyncGenerator[AioBaseClient, None]:
    """Клиент S3, настроенный на наш MinIO. Соединения закрываются при выходе из блока."""
    settings = get_minio_settings()
    async with session.client(
        "s3",
        endpoint_url=f"{settings.protocol}://{settings.host}:{settings.port}",
        aws_access_key_id=settings.root_user,
        aws_secret_access_key=settings.root_password,
        region_name=REGION,
        config=Config(
            signature_version="s3v4",
            # path-style: бакет в пути (host/bucket/key), а не в поддомене (bucket.host/key) —
            # поддомен у localhost не резолвится.
            s3={"addressing_style": "path"},
            # По умолчанию клиент повторяет недоступный запрос около 20 секунд — столько же
            # стартовало бы приложение без запущенного MinIO.
            retries={"max_attempts": 1},
            connect_timeout=CONNECT_TIMEOUT_SEC,
        ),
    ) as client:
        yield client


async def create_bucket() -> None:
    """Вызывается при каждом старте приложения, поэтому повторный вызов не ошибка."""
    settings = get_minio_settings()
    async with s3_client() as client:
        try:
            await client.create_bucket(Bucket=settings.bucket_name)
        except ClientError as exc:
            # Создаём сразу, а не «проверь, потом создай»: между проверкой и созданием
            # бакет может создать второй экземпляр приложения.
            if exc.response["Error"]["Code"] != BUCKET_EXISTS_CODE:
                raise


async def create_upload_url(key: str, content_type: str) -> str:
    """Presigned URL на загрузку: клиент делает PUT файла напрямую в хранилище.

    Content-Type входит в подпись — запрос с другим заголовком хранилище отклонит.
    """
    settings = get_minio_settings()
    async with s3_client() as client:
        return await client.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.bucket_name, "Key": key, "ContentType": content_type},
            ExpiresIn=settings.ttl_link_sec,
        )


async def create_download_url(key: str) -> str:
    """Presigned URL на чтение: бакет приватный, без подписи файл не отдаётся."""
    settings = get_minio_settings()
    async with s3_client() as client:
        return await client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.bucket_name, "Key": key},
            ExpiresIn=settings.ttl_link_sec,
        )


async def find_object_size(key: str) -> int | None:
    """Размер загруженного файла в байтах или None, если по ключу ничего не лежит."""
    settings = get_minio_settings()
    async with s3_client() as client:
        try:
            response = await client.head_object(Bucket=settings.bucket_name, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == NOT_FOUND_CODE:
                return None
            raise
    return response["ContentLength"]


async def delete_object(key: str) -> None:
    """Удаление несуществующего ключа в S3 не ошибка."""
    settings = get_minio_settings()
    async with s3_client() as client:
        await client.delete_object(Bucket=settings.bucket_name, Key=key)

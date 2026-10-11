from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aioboto3
from aiobotocore.client import AioBaseClient
from botocore.config import Config

from core.config import get_minio_settings

# MinIO регион не использует, но без него клиент не подпишет запрос.
REGION = "us-east-1"

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
        # path-style: бакет в пути (host/bucket/key), а не в поддомене (bucket.host/key) —
        # поддомен у localhost не резолвится.
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    ) as client:
        yield client

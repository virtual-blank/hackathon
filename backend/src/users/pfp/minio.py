import logging
import uuid

import aioboto3
import botocore
from botocore.exceptions import BotoCoreError, ClientError
from core.config import get_minio_settings
from uuid6 import uuid7

logger = logging.getLogger(__name__)

# ClientError — хранилище ответило отказом, BotoCoreError — до него не достучались.
STORAGE_ERRORS = (ClientError, BotoCoreError)
NOT_FOUND_CODE = "404"

MINIO_ENDPOINT = get_minio_settings().endpoint
BUCKET_NAME = get_minio_settings().bucket_name
ACCESS_KEY = get_minio_settings().root_user
SECRET_KEY = get_minio_settings().root_password

PUBLIC_PREFIX = f"{MINIO_ENDPOINT}/{BUCKET_NAME}/"
DEFAULT_PFP_URL = f"{PUBLIC_PREFIX}defaults/default-pfp.webp"


class MinioService:
    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            region_name="us-east-1",
        )
        self.endpoint_url = MINIO_ENDPOINT
        self.bucket_name = BUCKET_NAME

    def _get_client(self):
        config = botocore.client.Config(signature_version="s3v4")
        return self.session.client("s3", endpoint_url=self.endpoint_url, config=config)

    async def generate_presigned_upload_url(self, user_id: uuid.UUID, extension: str = "webp") -> dict[str, str]:
        file_key = f"pfp/{user_id}/{uuid7().hex}.{extension}"

        # Ссылка подписывается локально, без запроса в хранилище, поэтому ошибки здесь
        # не ловим: если она случилась, это неверная настройка, и её должно быть видно.
        async with self._get_client() as s3_client:
            presigned_url = await s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={"Bucket": self.bucket_name, "Key": file_key, "ContentType": f"image/{extension}"},
                ExpiresIn=get_minio_settings().ttl_link_sec,
            )
        public_url = f"{PUBLIC_PREFIX}{file_key}"
        return {"upload_url": presigned_url, "file_key": file_key, "public_url": public_url}

    async def find_object_size(self, file_key: str) -> int | None:
        """Размер загруженного файла в байтах или None, если по ключу ничего не лежит."""
        async with self._get_client() as s3_client:
            try:
                response = await s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            except ClientError as exc:
                if exc.response["Error"]["Code"] == NOT_FOUND_CODE:
                    return None
                raise
        return response["ContentLength"]

    async def delete_avatar(self, file_key: str) -> bool:
        """Не бросает: вызывается после записи в БД, и сбой хранилища не должен ронять запрос."""
        try:
            async with self._get_client() as s3_client:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
        except STORAGE_ERRORS:
            logger.exception("pfp: не удалось удалить файл %s", file_key)
            return False
        return True


minio_service = MinioService()

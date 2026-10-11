import aioboto3
import botocore
from botocore.exceptions import ClientError
from core.config import get_minio_settings
from uuid6 import uuid7

MINIO_ENDPOINT = get_minio_settings().endpoint
BUCKET_NAME = get_minio_settings().bucket_name
ACCESS_KEY = get_minio_settings().root_user
SECRET_KEY = get_minio_settings().root_password


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

    async def generate_presigned_upload_url(self, extension: str = "webp"):
        unique_filename = f"{uuid7().hex}.{extension}"
        file_key = f"pfp/{unique_filename}"

        try:
            async with self._get_client() as s3_client:
                presigned_url = await s3_client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={"Bucket": self.bucket_name, "Key": file_key, "ContentType": f"image/{extension}"},
                    ExpiresIn=300,  # 5 min
                )

                public_url = f"{self.endpoint_url}/{self.bucket_name}/{file_key}"

                return {"upload_url": presigned_url, "file_key": file_key, "public_url": public_url}
        except ClientError as e:
            print(f"S3 Presign Error: {e!s}")
            return None
        except Exception as e:
            print(f"S3 Unexpected Error: {e!s}")
            return None

    async def delete_avatar(self, file_key: str) -> bool:
        try:
            async with self._get_client() as s3_client:
                await s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
                print(f"[+] S3 successfully deleted {file_key}")
                return True
        except ClientError as e:
            print(f"S3 Delete Error: {e!s}")
            return False
        except Exception as e:
            print(f"S3 Unexpected Error While Delete {file_key}: {e!s}")
            return False


minio_service = MinioService()

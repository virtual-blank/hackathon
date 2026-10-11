from fastapi import APIRouter, HTTPException, status
from src.auth.deps import CurrentUserDep, CurrentUserIdDep, SessionDep
from src.users.pfp.minio import BUCKET_NAME, MINIO_ENDPOINT, minio_service
from src.users.pfp.schemas import ExtensionSchema, PfpUpdateRequest, UploadUrlResponse

router = APIRouter(prefix="/users/me/pfp", tags=["🖼 User Profile Picture"])

PUBLIC_PREFIX = f"{MINIO_ENDPOINT}/{BUCKET_NAME}/"


# == GET PRESIGNED URL ==
@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_pfp_upload_url(extension_dto: ExtensionSchema, user_id: CurrentUserIdDep):
    result = await minio_service.generate_presigned_upload_url(user_id, extension_dto.extension)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать ссылку для загрузки",
        )
    return result


# == SAVE PFP IN DB ==
@router.put("")
async def update_pfp(data: PfpUpdateRequest, user: CurrentUserDep, session: SessionDep):
    if not data.file_key.startswith(f"pfp/{user.id}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Чужой файл")
    new_url = f"{PUBLIC_PREFIX}{data.file_key}"
    old_url = user.pfp_url
    if old_url == new_url:
        return {"pfp_url": new_url}
    user.pfp_url = new_url
    await session.commit()
    if old_url and old_url.startswith(PUBLIC_PREFIX):
        await minio_service.delete_avatar(old_url.removeprefix(PUBLIC_PREFIX))
    return {"pfp_url": new_url}

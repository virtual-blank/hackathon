from fastapi import APIRouter, HTTPException, status
from src.auth.deps import CurrentUserDep, CurrentUserIdDep, SessionDep
from src.users.pfp.minio import PUBLIC_PREFIX, minio_service
from src.users.pfp.schemas import ExtensionSchema, PfpUpdateRequest, UploadUrlResponse

router = APIRouter(prefix="/users/me/pfp", tags=["🖼 User Profile Picture"])


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

    old_key = old_url.removeprefix(PUBLIC_PREFIX) if old_url else None
    if old_key and old_key.startswith("pfp/"):
        await minio_service.delete_avatar(old_key)

    return {"pfp_url": new_url}

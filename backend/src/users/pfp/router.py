from fastapi import APIRouter, HTTPException, status
from src.auth.deps import CurrentUserDep, CurrentUserIdDep, SessionDep
from src.users.pfp.minio import PUBLIC_PREFIX, minio_service
from src.users.pfp.schemas import ExtensionSchema, PfpUpdateRequest, UploadUrlResponse

router = APIRouter(prefix="/users/me/pfp", tags=["🖼 User Profile Picture"])

MAX_PFP_SIZE_BYTES = 5 * 1024 * 1024


# == GET PRESIGNED URL ==
@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_pfp_upload_url(extension_dto: ExtensionSchema, user_id: CurrentUserIdDep):
    return await minio_service.generate_presigned_upload_url(user_id, extension_dto.extension)


# == SAVE PFP IN DB ==
@router.put("")
async def update_pfp(data: PfpUpdateRequest, user: CurrentUserDep, session: SessionDep):
    if not data.file_key.startswith(f"pfp/{user.id}/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Чужой файл")

    new_url = f"{PUBLIC_PREFIX}{data.file_key}"
    old_url = user.pfp_url

    if old_url == new_url:
        return {"pfp_url": new_url}

    # Клиент мог получить ссылку и ничего не загрузить — без проверки в профиль
    # попала бы ссылка на несуществующий файл.
    size = await minio_service.find_object_size(data.file_key)
    if size is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не загружен")
    if size > MAX_PFP_SIZE_BYTES:
        # Presigned PUT не умеет ограничивать размер, поэтому проверяем после загрузки.
        await minio_service.delete_avatar(data.file_key)
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Файл больше 5 МБ")

    user.pfp_url = new_url
    await session.commit()

    old_key = old_url.removeprefix(PUBLIC_PREFIX) if old_url else None
    if old_key and old_key.startswith("pfp/"):
        await minio_service.delete_avatar(old_key)

    return {"pfp_url": new_url}


# == DELETE PFP ==
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pfp(user: CurrentUserDep, session: SessionDep) -> None:
    old_url = user.pfp_url
    if old_url is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фото профиля не установлено")

    # Сначала БД, потом файл: при сбое между шагами останется лишний файл,
    # а не профиль со ссылкой на удалённый.
    user.pfp_url = None
    await session.commit()

    old_key = old_url.removeprefix(PUBLIC_PREFIX)
    if old_key.startswith("pfp/"):
        await minio_service.delete_avatar(old_key)

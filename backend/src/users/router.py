from fastapi import APIRouter, HTTPException, status
from src.auth.deps import CurrentUserDep, SessionDep
from src.exceptions.avatar_exceptions import AvatarFileNotFoundError, AvatarNotFoundError, AvatarTooLargeError
from src.users.schemas import (
    AuthOutputSchema,
    AvatarOutputSchema,
    AvatarSetSchema,
    AvatarUploadCreateSchema,
    AvatarUploadOutputSchema,
    UserCreateSchema,
    UserLoginSchema,
)
from src.users.service import UsersService

router = APIRouter(prefix="/users", tags=["👤 Users"])


# == SIGN UP ==
@router.post("/sign-up", status_code=status.HTTP_201_CREATED, response_model=AuthOutputSchema, description="Sign-Up")
async def sign_up(user_data: UserCreateSchema, session: SessionDep):
    service = UsersService(session=session)
    try:
        return await service.sign_up(user_data=user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == LOGIN ==
@router.post("/login", status_code=status.HTTP_200_OK, response_model=AuthOutputSchema, description="Login")
async def login(user_data: UserLoginSchema, session: SessionDep):
    service = UsersService(session=session)
    try:
        return await service.login(user_data=user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# todo: кастомные exception


# == AVATAR ==
@router.post(
    "/me/avatar-uploads",
    status_code=status.HTTP_201_CREATED,
    response_model=AvatarUploadOutputSchema,
    description="Шаг 1: получить presigned URL и загрузить по нему файл методом PUT с тем же Content-Type",
)
async def create_avatar_upload(
    upload_data: AvatarUploadCreateSchema, user: CurrentUserDep, session: SessionDep
) -> AvatarUploadOutputSchema:
    service = UsersService(session=session)
    return await service.create_avatar_upload(user=user, content_type=upload_data.content_type)


@router.put(
    "/me/avatar",
    status_code=status.HTTP_200_OK,
    response_model=AvatarOutputSchema,
    description="Шаг 2: назначить загруженный файл фото профиля. Прежнее фото удаляется",
)
async def set_avatar(avatar_data: AvatarSetSchema, user: CurrentUserDep, session: SessionDep) -> AvatarOutputSchema:
    service = UsersService(session=session)
    try:
        return await service.set_avatar(user=user, key=avatar_data.key)
    except AvatarFileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AvatarTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc


@router.get(
    "/me/avatar",
    status_code=status.HTTP_200_OK,
    response_model=AvatarOutputSchema,
    description="Временная ссылка на фото профиля",
)
async def get_avatar(user: CurrentUserDep, session: SessionDep) -> AvatarOutputSchema:
    service = UsersService(session=session)
    try:
        return await service.get_avatar(user=user)
    except AvatarNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/me/avatar", status_code=status.HTTP_204_NO_CONTENT, description="Удалить фото профиля")
async def delete_avatar(user: CurrentUserDep, session: SessionDep) -> None:
    service = UsersService(session=session)
    try:
        await service.delete_avatar(user=user)
    except AvatarNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# == LOG OUT ==
# == REFRESH TOKEN ==
# == DELETE ACCOUNT ==

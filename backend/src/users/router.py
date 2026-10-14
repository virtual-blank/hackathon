from fastapi import APIRouter, HTTPException, status

from src.auth.deps import CurrentUserDep, CurrentUserIdDep, SessionDep
from src.users.schemas import (
    AuthOutputSchema,
    RefreshTokenSchema,
    UserCreateSchema,
    UserLoginSchema,
    UserPasswordUpdateSchema,
    UserUpdateSchema,
    UserOutputSchema
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


# == LOGIN ==
@router.post("/login", status_code=status.HTTP_200_OK, response_model=AuthOutputSchema, description="Login")
async def login(user_data: UserLoginSchema, session: SessionDep):
    service = UsersService(session=session)
    try:
        return await service.login(user_data=user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

# == LOG OUT ==
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Logout",
)
async def logout(user: CurrentUserDep, session: SessionDep):
    """Отзывает все refresh-токены юзера. Access умрёт сам через exp."""
    service = UsersService(session=session)
    try:
        await service.logout(user_id=user.id)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return None


# == REFRESH TOKEN ==
@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AuthOutputSchema,
    description="Refresh access token",
)
async def refresh(payload: RefreshTokenSchema, session: SessionDep):
    service = UsersService(session=session)
    try:
        return await service.refresh(refresh_token_str=payload.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

# == DELETE ACCOUNT ==
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, description="Delete my account",)
async def delete_account(user: CurrentUserDep, session: SessionDep):
    service = UsersService(session=session)
    try:
        await service.delete_account(user_id=user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return None


# == GET ME ==
@router.get("/me", status_code=status.HTTP_200_OK, response_model=UserOutputSchema, description="Get user's profile")
async def get_me(
    current_user_id: CurrentUserIdDep,
    session: SessionDep
):
    service = UsersService(session=session)
    try:
        return await service.get_me(user_id=current_user_id)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return None


# == PATCH ME ==
@router.patch("/me", status_code=status.HTTP_200_OK, response_model=UserOutputSchema, description="Edit user's profile")
async def edit_profile(
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
    user_data: UserUpdateSchema
):
    service = UsersService(session=session)
    try:
        return await service.edit_profile(
            user_id=current_user_id,
            user_data=user_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return None

# == UPDATE PASSWORD ==
@router.patch("/password", status_code=status.HTTP_200_OK, response_model=AuthOutputSchema, description="Edit user's password")
async def change_password(
    current_user_id: CurrentUserIdDep,
    session: SessionDep,
    new_password_dto: UserPasswordUpdateSchema
):
    service = UsersService(session=session)
    try:
        return await service.change_password(
            user_id=current_user_id,
            new_password_dto=new_password_dto
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    

# todo: кастомные exception

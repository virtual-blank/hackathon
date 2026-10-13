from fastapi import APIRouter, HTTPException, status
from src.auth.deps import SessionDep, CurrentUserDep
from src.users.schemas import AuthOutputSchema, RefreshTokenSchema, UserCreateSchema, UserLoginSchema
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

# todo: кастомные exception

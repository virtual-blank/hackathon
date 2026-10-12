from fastapi import APIRouter, HTTPException, status
from src.auth.deps import SessionDep
from src.users.schemas import AuthOutputSchema, UserCreateSchema, UserLoginSchema
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


# == LOG OUT ==
# == REFRESH TOKEN ==
# == DELETE ACCOUNT ==

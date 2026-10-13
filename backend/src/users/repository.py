import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import User


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, username: str, password_hash: str, email: str) -> User:
        new_user = User(username=username, password_hash=password_hash, email=email)
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, delete, or_, select, update
from src.social.enums import RelationStatus
from src.social.models import UserRelation
from src.users.models import RefreshToken, User, UserAchievement


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _commit(self):
        await self.session.commit()

    async def _rollback(self):
        await self.session.rollback()

    async def create_user(self, username: str, password_hash: str, email: str) -> User:
        new_user = User(username=username, password_hash=password_hash, email=email, achievements=[])
        self.session.add(new_user)
        await self.session.commit()

        return new_user

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.achievements).joinedload(UserAchievement.achievement))
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = (
            select(User)
            .where(User.username == username)
            .options(selectinload(User.achievements).joinedload(UserAchievement.achievement))
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_telegram_hash(self, token_hash: str) -> User | None:
        stmt = select(User).where(User.telegram_link_token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_telegram_chat_id(self, chat_id: int) -> User | None:
        stmt = select(User).where(User.telegram_chat_id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        new_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(new_token)
        await self.session.commit()
        return new_token

    async def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_id: uuid.UUID) -> None:
        stmt = update(RefreshToken).where(RefreshToken.id == token_id).values(revoked_at=datetime.now(UTC))
        await self.session.execute(stmt)
        await self.session.commit()

    async def revoke_all_user_refresh_tokens(self, user_id: uuid.UUID) -> None:
        """Отозвать все refresh юзера — при подозрении на кражу или logout."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def edit_profile(
        self,
        user_id: uuid.UUID,
        user_data_dict: dict,
    ):
        stmt = update(User).where(User.id == user_id).values(**user_data_dict).returning(User)
        result = await self.session.execute(stmt)
        await self._commit()
        return result.scalar_one_or_none()

    async def search_users(self, query: str, exclude_user_id: uuid.UUID, limit: int) -> list[User]:
        # экранирование
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        blocked = select(UserRelation.id).where(
            UserRelation.status == RelationStatus.BLOCKED,
            or_(
                and_(UserRelation.user_id == exclude_user_id, UserRelation.target_id == User.id),
                and_(UserRelation.target_id == exclude_user_id, UserRelation.user_id == User.id),
            ),
        )
        stmt = (
            select(User)
            .where(
                User.id != exclude_user_id,
                User.username.ilike(f"%{escaped}%", escape="\\"),
                ~blocked.exists(),
            )
            .order_by(User.username)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

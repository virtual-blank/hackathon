import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions.friends_exceptions import FriendsConflictError, FriendsNotFoundError
from src.friends.models import UserRelation
from src.friends.repository import FriendsRepository
from src.friends.schemas import FriendRequestsSchema, FriendSchema, RelationStatusSchema
from src.social.enums import RelationStatus
from src.users.repository import UsersRepository


class FriendsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FriendsRepository(session=session)
        self.users_repo = UsersRepository(session=session)

    async def send_request(self, user_id: uuid.UUID, target_id: uuid.UUID) -> RelationStatusSchema:
        await self._check_target(user_id=user_id, target_id=target_id)
        relations = await self.repo.get_pair_relations(user_id, target_id)

        statuses = {relation.status for relation in relations}
        if RelationStatus.BLOCKED in statuses:
            # Кто кого заблокировал, не уточняем: о чужой блокировке пользователю знать не нужно.
            raise FriendsConflictError("Нельзя отправить заявку этому пользователю")
        if RelationStatus.ACCEPTED in statuses:
            raise FriendsConflictError("Вы уже друзья")

        incoming = self._find(relations, sender_id=target_id, status=RelationStatus.PENDING)
        if incoming is not None:
            # Встречная заявка уже лежит — значит, оба согласны, сразу дружим.
            incoming.status = RelationStatus.ACCEPTED
            await self.session.commit()
            return RelationStatusSchema(status=RelationStatus.ACCEPTED)

        if self._find(relations, sender_id=user_id, status=RelationStatus.PENDING) is not None:
            raise FriendsConflictError("Заявка уже отправлена")

        self.repo.add_relation(user_id=user_id, target_id=target_id, status=RelationStatus.PENDING)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            # Такой же запрос успел пройти между нашей проверкой и вставкой — сработал unique (user_id, target_id).
            await self.session.rollback()
            raise FriendsConflictError("Заявка уже отправлена") from exc
        return RelationStatusSchema(status=RelationStatus.PENDING)

    async def accept_request(self, user_id: uuid.UUID, sender_id: uuid.UUID) -> RelationStatusSchema:
        request = await self._get_incoming_request(user_id=user_id, sender_id=sender_id)
        request.status = RelationStatus.ACCEPTED
        await self.session.commit()
        return RelationStatusSchema(status=RelationStatus.ACCEPTED)

    async def decline_request(self, user_id: uuid.UUID, sender_id: uuid.UUID) -> None:
        request = await self._get_incoming_request(user_id=user_id, sender_id=sender_id)
        await self.repo.delete_relation(request)
        await self.session.commit()

    async def delete_friend(self, user_id: uuid.UUID, friend_id: uuid.UUID) -> None:
        relations = await self.repo.get_pair_relations(user_id, friend_id)
        friendship = next((relation for relation in relations if relation.status == RelationStatus.ACCEPTED), None)
        if friendship is None:
            raise FriendsNotFoundError("Этого пользователя нет в друзьях")
        await self.repo.delete_relation(friendship)
        await self.session.commit()

    async def block_user(self, user_id: uuid.UUID, target_id: uuid.UUID) -> RelationStatusSchema:
        await self._check_target(user_id=user_id, target_id=target_id)
        relations = await self.repo.get_pair_relations(user_id, target_id)

        # Заявка и дружба разрываются; встречную блокировку не трогаем — она чужая.
        for relation in relations:
            if relation.status != RelationStatus.BLOCKED:
                await self.repo.delete_relation(relation)

        if self._find(relations, sender_id=user_id, status=RelationStatus.BLOCKED) is None:
            # flush: удаление должно уйти в БД раньше вставки, иначе сработает unique (user_id, target_id).
            await self.session.flush()
            self.repo.add_relation(user_id=user_id, target_id=target_id, status=RelationStatus.BLOCKED)

        await self.session.commit()
        return RelationStatusSchema(status=RelationStatus.BLOCKED)

    async def get_friends(self, user_id: uuid.UUID, limit: int, offset: int) -> list[FriendSchema]:
        friends = await self.repo.get_friends(user_id=user_id, limit=limit, offset=offset)
        return [FriendSchema.model_validate(friend) for friend in friends]

    async def get_requests(self, user_id: uuid.UUID, limit: int) -> FriendRequestsSchema:
        incoming = await self.repo.get_incoming_requests(user_id=user_id, limit=limit)
        outgoing = await self.repo.get_outgoing_requests(user_id=user_id, limit=limit)
        return FriendRequestsSchema(
            incoming=[FriendSchema.model_validate(user) for user in incoming],
            outgoing=[FriendSchema.model_validate(user) for user in outgoing],
        )

    async def _check_target(self, user_id: uuid.UUID, target_id: uuid.UUID) -> None:
        if user_id == target_id:
            raise FriendsConflictError("Нельзя выполнить это действие с самим собой")
        if await self.users_repo.get_user_by_id(target_id) is None:
            raise FriendsNotFoundError("Пользователь не найден")

    async def _get_incoming_request(self, user_id: uuid.UUID, sender_id: uuid.UUID) -> UserRelation:
        relations = await self.repo.get_pair_relations(user_id, sender_id)
        request = self._find(relations, sender_id=sender_id, status=RelationStatus.PENDING)
        if request is None:
            raise FriendsNotFoundError("Заявка не найдена")
        return request

    @staticmethod
    def _find(relations: list[UserRelation], sender_id: uuid.UUID, status: RelationStatus) -> UserRelation | None:
        """Строка с нужным статусом, которую создал sender_id."""
        for relation in relations:
            if relation.user_id == sender_id and relation.status == status:
                return relation
        return None

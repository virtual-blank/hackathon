class FriendsNotFoundError(Exception):
    """Нет пользователя, заявки или дружбы, с которыми просят что-то сделать."""


class FriendsConflictError(Exception):
    """Действие невозможно при текущей связи между пользователями."""

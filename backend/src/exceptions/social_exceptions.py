class SocialError(Exception):
    """Базовое исключение модуля соцсвязей и чатов."""


class ChatWithSelfError(SocialError):
    """Нельзя вести переписку с самим собой."""


class NotFriendsError(SocialError):
    """Переписка доступна только друзьям: статус accepted в user_relations."""


class UserBlockedError(SocialError):
    """Один из пользователей заблокировал другого."""


class MessageNotFoundError(SocialError):
    """Сообщение не найдено или адресовано не мне."""

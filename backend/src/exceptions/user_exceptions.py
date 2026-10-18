class UsernameTakenError(Exception):
    """Юзернейм или почта заняты"""


class IncorrectPassword(Exception):
    """Не верный пароль"""


class AuthError(Exception):
    """Ошибки авторизации"""


class UserNotFoundError(Exception):
    """Пользователь не найден"""


class DataFormatError(Exception):
    """Ошибка входящих данных"""

class AvatarNotFoundError(Exception):
    """У пользователя нет фото профиля."""


class AvatarFileNotFoundError(Exception):
    """По ключу нет файла: его не загрузили или ключ принадлежит другому пользователю."""


class AvatarTooLargeError(Exception):
    """Загруженный файл больше допустимого размера."""

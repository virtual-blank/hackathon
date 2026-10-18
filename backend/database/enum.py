import enum
from sqlalchemy import Enum


def str_enum(enum_cls: type[enum.Enum], length: int = 16) -> Enum:
    """
    Enum без нативного типа Postgres: VARCHAR + CHECK.
    - значения хранятся как "pending", а не "PENDING" (имя члена);
    - новые значения добавляются обычной миграцией, без ALTER TYPE.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=length,
        name=enum_cls.__name__.lower(),
        values_callable=lambda e: [m.value for m in e],
    )

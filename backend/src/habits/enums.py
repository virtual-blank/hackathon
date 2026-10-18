import enum


class Visibility(enum.StrEnum):
    PRIVATE = "private"  # только владелец (и партнёр по совместной привычке)
    FRIENDS = "friends"  # владелец и друзья
    PUBLIC = "public"  # любой пользователь, кроме заблокированных


class InviteStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"

import enum


class RelationStatus(enum.StrEnum):
    PENDING = "pending"  # user_id отправил заявку target_id
    ACCEPTED = "accepted"  # дружба (направление не важно)
    BLOCKED = "blocked"  # user_id заблокировал target_id

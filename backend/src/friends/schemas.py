import uuid

from pydantic import BaseModel, ConfigDict, field_validator

from src.social.enums import RelationStatus
from src.users.pfp.minio import DEFAULT_PFP_URL


class FriendSchema(BaseModel):
    # берётся из User
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    pfp_url: str

    @field_validator("pfp_url", mode="before")
    @classmethod
    def set_default_pfp(cls, v: str | None) -> str:
        return v or DEFAULT_PFP_URL


class FriendRequestsSchema(BaseModel):
    incoming: list[FriendSchema]
    outgoing: list[FriendSchema]


class RelationStatusSchema(BaseModel):
    status: RelationStatus

from pydantic import BaseModel, ConfigDict, field_validator

from src.achievements.models import RuleTypeEnum
from src.users.pfp.minio import ACHIEVEMENTS_PREFIX


class AchievementOutputSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    rule_type: RuleTypeEnum
    rule_value: int
    color_hex: str
    requierement: str
    description: str
    icon_url: str

    @field_validator("icon_url", mode="after")
    @classmethod
    def build_url(cls, v: str) -> str:
        return v if v.startswith("http") else f"{ACHIEVEMENTS_PREFIX}{v}"

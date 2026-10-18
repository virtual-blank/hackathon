from pydantic import BaseModel, ConfigDict, Field


class TelegramLinkOutputSchema(BaseModel):
    url: str = Field(..., description="Ссылка вида https://t.me/<bot_name>?start=<code>")


class TelegramChatSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int


class TelegramUserSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    is_bot: bool = False
    username: str | None = None
    first_name: str | None = None


class TelegramMessageSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message_id: int
    chat: TelegramChatSchema
    from_: TelegramUserSchema | None = Field(default=None, alias="from")
    text: str | None = None


class TelegramWebhookSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    update_id: int
    message: TelegramMessageSchema | None = None

import re
from typing import Literal

from pydantic import BaseModel, field_validator

FILE_KEY_RE = re.compile(r"pfp/[0-9a-f\-]{36}/[0-9a-f]{32}\.(png|webp|jpeg)")


class UploadUrlResponse(BaseModel):
    upload_url: str
    file_key: str
    public_url: str


class ExtensionSchema(BaseModel):
    extension: Literal["png", "webp", "jpeg"] = "webp"


class PfpUpdateRequest(BaseModel):
    file_key: str

    @field_validator("file_key")
    @classmethod
    def check_file_key(cls, v: str) -> str:
        if not FILE_KEY_RE.fullmatch(v):
            raise ValueError("Неверный file_key")
        return v

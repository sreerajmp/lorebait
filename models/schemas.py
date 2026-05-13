from pydantic import BaseModel, Field, field_validator

from models.persona import Persona


class IndexRequest(BaseModel):
    directory_path: str = Field(
        ...,
        min_length=1,
        description="Absolute or user-relative local folder path to index.",
    )

    @field_validator("directory_path")
    @classmethod
    def directory_path_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("directory_path cannot be blank")
        return stripped


class IndexResponse(BaseModel):
    status: str
    directory_path: str
    message: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    persona: Persona | None = Field(
        default=None,
        description="Optional persona override. Persists as active persona when supplied.",
    )
    folder_path: str | None = Field(
        default=None,
        description="Optional folder override. Persists as active folder when supplied.",
    )
    top_k: int = Field(default=4, ge=1, le=12)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message cannot be blank")
        return stripped

    @field_validator("folder_path")
    @classmethod
    def folder_path_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("folder_path cannot be blank")
        return stripped


class SessionUpdateRequest(BaseModel):
    active_folder: str | None = None
    active_persona: Persona | None = None

    @field_validator("active_folder")
    @classmethod
    def active_folder_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("active_folder cannot be blank")
        return stripped


class SessionResponse(BaseModel):
    active_folder: str | None
    active_persona: Persona

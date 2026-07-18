from pydantic import BaseModel, ConfigDict, Field, field_validator

class StatusRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    token: str = Field(min_length=1, max_length=256)

    company: str = Field(min_length=1, max_length=128)
    office: str = Field(default="", max_length=128)
    resource: str = Field(default="", max_length=128)
    server: str = Field(default="", max_length=128)
    type: str = Field(default="", max_length=64)

    status: bool | None = None
    message: str | None = Field(default=None, max_length=3900)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
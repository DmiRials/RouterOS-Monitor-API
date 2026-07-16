from pydantic import BaseModel


class StatusRequest(BaseModel):
    token: str

    company: str
    office: str = ""
    resource: str = ""
    server: str = ""
    type: str = ""

    # Для Netwatch
    status: bool | None = None

    # Произвольное сообщение
    message: str | None = None
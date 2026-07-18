from html import escape

from app.config import settings
from app.models import StatusRequest

def _trim(text: str) -> str:
    return text[:settings.MESSAGE_MAX_LENGTH]

def format_message(data: StatusRequest) -> str:
    if data.message:
        title = escape(data.company)
        if data.office:
            title += f" | {escape(data.office)}"
        return _trim(
            f"🚨 {title}\n\n"
            f"{escape(data.message)}"
        )

    if data.status is None:
        return "⚠️ Получено событие без status и message."

    icon = "✅" if data.status else "❌"
    status = "доступен" if data.status else "недоступен"
    parts = [escape(data.company)]

    if data.office:
        parts.append(escape(data.office))

    if data.resource:
        parts.append(escape(data.resource))

    if data.server:
        parts.append(escape(data.server))

    if data.type:
        parts.append(escape(data.type))

    return _trim(f"{icon} {' | '.join(parts)} | {status}")
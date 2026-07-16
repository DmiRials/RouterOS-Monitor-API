from app.models import StatusRequest


def format_message(data: StatusRequest) -> str:
    """
    Формирование сообщения для Telegram.
    """

    #
    # Если передано готовое сообщение
    #
    if data.message:

        title = data.company

        if data.office:
            title += f" | {data.office}"

        return (
            f"🚨 {title}\n\n"
            f"{data.message}"
        )

    #
    # Для Netwatch status обязателен
    #
    if data.status is None:
        return "⚠️ Получено событие без status и message."

    icon = "✅" if data.status else "❌"
    status = "доступен" if data.status else "недоступен"

    parts = [data.company]

    if data.office:
        parts.append(data.office)

    if data.resource:
        parts.append(data.resource)

    if data.server:
        parts.append(data.server)

    if data.type:
        parts.append(data.type)

    return f"{icon} {' | '.join(parts)} | {status}"
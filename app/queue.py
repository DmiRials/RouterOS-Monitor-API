import asyncio
from dataclasses import dataclass

from app.config import settings

@dataclass(slots=True)
class TelegramTask:
    request_id: str
    text: str

telegram_queue: asyncio.Queue[TelegramTask] = asyncio.Queue(
    maxsize=settings.QUEUE_MAX_SIZE
)
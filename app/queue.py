import asyncio
from dataclasses import dataclass


@dataclass(slots=True)
class TelegramTask:
    request_id: str
    text: str


telegram_queue: asyncio.Queue[TelegramTask] = asyncio.Queue()
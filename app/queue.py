import asyncio
from dataclasses import dataclass

@dataclass(slots=True)
class TelegramTask:
    request_id: str
    text: str

class EventQueue:
    def __init__(self, max_size: int) -> None:
        self.items: asyncio.Queue[TelegramTask] = asyncio.Queue(maxsize=max_size)

    def put_nowait(self, task: TelegramTask) -> None:
        self.items.put_nowait(task)

    async def get(self) -> TelegramTask:
        return await self.items.get()

    def task_done(self) -> None:
        self.items.task_done()

    async def join(self) -> None:
        await self.items.join()

    def qsize(self) -> int:
        return self.items.qsize()

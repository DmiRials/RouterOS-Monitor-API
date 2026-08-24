from dataclasses import dataclass
from typing import Protocol

from app.cache import status_cache_key
from app.formatter import format_message
from app.models import StatusRequest
from app.queue import TelegramTask


class TokenChecker(Protocol):
    def check(self, token: str) -> bool: ...


class StatusStore(Protocol):
    def is_same(self, key: str, status: bool) -> bool: ...
    def remember(self, key: str, status: bool) -> None: ...


class TaskQueue(Protocol):
    def put_nowait(self, task: TelegramTask) -> None: ...


@dataclass(frozen=True, slots=True)
class AcceptResult:
    queued: bool
    duplicate: bool = False


class EventService:
    def __init__(self, tokens: TokenChecker, statuses: StatusStore, queue: TaskQueue) -> None:
        self.tokens = tokens
        self.statuses = statuses
        self.queue = queue

    def accept(self, data: StatusRequest, request_id: str) -> AcceptResult:
        if not self.tokens.check(data.token):
            raise PermissionError("Invalid token")

        cache_key = None
        if data.status is not None and not data.message:
            cache_key = status_cache_key(
                data.company, data.office, data.resource, data.server, data.type
            )
            if self.statuses.is_same(cache_key, data.status):
                return AcceptResult(queued=False, duplicate=True)

        text = format_message(data)
        self.queue.put_nowait(TelegramTask(request_id=request_id, text=text))

        if cache_key is not None and data.status is not None:
            self.statuses.remember(cache_key, data.status)
        return AcceptResult(queued=True)

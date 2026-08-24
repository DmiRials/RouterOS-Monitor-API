import unittest
import os
from asyncio import QueueFull

os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("CHAT_ID", "test-chat")

from pydantic import ValidationError

from app.cache import StatusCache
from app.models import StatusRequest
from app.services import EventService


class FakeTokens:
    def check(self, token: str) -> bool:
        return token == "valid"


class FakeQueue:
    def __init__(self, full: bool = False) -> None:
        self.full = full
        self.tasks = []

    def put_nowait(self, task) -> None:
        if self.full:
            raise QueueFull
        self.tasks.append(task)


class EventServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.queue = FakeQueue()
        self.service = EventService(FakeTokens(), StatusCache(), self.queue)

    def test_queues_status_and_skips_duplicate(self) -> None:
        request = StatusRequest(token="valid", company="Office", status=False)

        first = self.service.accept(request, "REQUEST1")
        second = self.service.accept(request, "REQUEST2")

        self.assertTrue(first.queued)
        self.assertTrue(second.duplicate)
        self.assertEqual(len(self.queue.tasks), 1)

    def test_does_not_remember_status_when_queue_is_full(self) -> None:
        statuses = StatusCache()
        service = EventService(FakeTokens(), statuses, FakeQueue(full=True))
        request = StatusRequest(token="valid", company="Office", status=True)

        with self.assertRaises(QueueFull):
            service.accept(request, "REQUEST1")

        replacement_queue = FakeQueue()
        service = EventService(FakeTokens(), statuses, replacement_queue)
        self.assertTrue(service.accept(request, "REQUEST2").queued)

    def test_rejects_invalid_token(self) -> None:
        request = StatusRequest(token="invalid", company="Office", status=True)

        with self.assertRaises(PermissionError):
            self.service.accept(request, "REQUEST1")

    def test_message_is_html_escaped(self) -> None:
        request = StatusRequest(
            token="valid", company="<Office>", message="<b>alarm</b>"
        )

        self.service.accept(request, "REQUEST1")

        self.assertIn("&lt;Office&gt;", self.queue.tasks[0].text)
        self.assertIn("&lt;b&gt;alarm&lt;/b&gt;", self.queue.tasks[0].text)

    def test_requires_status_or_message(self) -> None:
        with self.assertRaises(ValidationError):
            StatusRequest(token="valid", company="Office")

    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ValidationError):
            StatusRequest(token="valid", company="Office", status=True, unknown=1)


if __name__ == "__main__":
    unittest.main()

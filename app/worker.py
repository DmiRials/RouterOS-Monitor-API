import asyncio
import json

import httpx

from app.config import settings
from app.logger import logger
from app.queue import EventQueue, TelegramTask
from app.telegram import Telegram


async def telegram_worker(
    queue: EventQueue,
    telegram: Telegram,
    stop_event: asyncio.Event,
) -> None:
    logger.info("WORKER     | Telegram Worker запущен")
    while not stop_event.is_set():
        try:
            task: TelegramTask = await asyncio.wait_for(queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            continue

        try:
            await _send_with_retries(task, telegram)
        finally:
            queue.task_done()


async def _send_with_retries(task: TelegramTask, telegram: Telegram) -> None:
    sent = False
    max_retries = max(settings.TELEGRAM_MAX_RETRIES, 1)

    for attempt in range(1, max_retries + 1):
        delay = 0
        try:
            response = await telegram.send(task.text)
            logger.info(
                f"[{task.request_id}] {'TELEGRAM':<10} | "
                f"HTTP {response.status_code} (attempt {attempt})"
            )

            if response.status_code == 200:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {}
                if response_data.get("ok") is True:
                    logger.info(f"[{task.request_id}] {'TELEGRAM':<10} | OK")
                    sent = True
                    break

            if response.status_code == 429:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {}
                retry_after = response_data.get("parameters", {}).get("retry_after", 5)
                try:
                    retry_after = int(retry_after)
                except (TypeError, ValueError):
                    retry_after = 5
                delay = min(max(retry_after, 1), settings.TELEGRAM_RETRY_AFTER_MAX)
                logger.warning(
                    f"[{task.request_id}] {'TELEGRAM':<10} | FLOOD WAIT {delay}s"
                )
            elif 500 <= response.status_code < 600:
                delay = min(2 ** attempt, 30)
                logger.warning(
                    f"[{task.request_id}] {'TELEGRAM':<10} | "
                    f"RETRY HTTP {response.status_code}"
                )
            else:
                logger.error(
                    f"[{task.request_id}] {'TELEGRAM':<10} | "
                    f"HTTP {response.status_code}"
                )
                break
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError) as exc:
            delay = min(2 ** attempt, 30)
            logger.warning(
                f"[{task.request_id}] {'TELEGRAM':<10} | "
                f"HTTP CLIENT ERROR (attempt {attempt}): {exc}"
            )
        except Exception:
            logger.exception(
                f"[{task.request_id}] {'WORKER':<10} | UNEXPECTED ERROR"
            )
            break

        if attempt < max_retries and delay:
            await asyncio.sleep(delay)

    if not sent:
        logger.error(
            f"[{task.request_id}] {'TELEGRAM':<10} | "
            f"FAILED AFTER {max_retries} ATTEMPTS"
        )

import asyncio
import json

from app.config import settings
from app.logger import logger
from app.queue import TelegramTask, telegram_queue
from app.telegram import telegram

async def telegram_worker():
    logger.info("WORKER     | Telegram Worker запущен")
    while True:
        task: TelegramTask = await telegram_queue.get()
        logger.info(
            f"[{task.request_id}] {'WORKER':<10} | PROCESS"
        )

        sent = False
        for attempt in range(1, settings.TELEGRAM_MAX_RETRIES + 1):
            try:
                response = await telegram.send(task.text)
                logger.info(
                    f"[{task.request_id}] {'TELEGRAM':<10} | HTTP {response.status_code} (attempt {attempt})"
                )

                if response.status_code == 200:
                    logger.info(
                        f"[{task.request_id}] {'TELEGRAM':<10} | OK"
                    )
                    sent = True
                    break

                if response.status_code == 429:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        data = {}

                    retry = data.get(
                        "parameters",
                        {}
                    ).get(
                        "retry_after",
                        5
                    )

                    logger.warning(
                        f"[{task.request_id}] {'TELEGRAM':<10} | FLOOD WAIT {retry}s"
                    )
                    await asyncio.sleep(retry)
                    continue

                if 500 <= response.status_code < 600:
                    logger.warning(
                        f"[{task.request_id}] {'TELEGRAM':<10} | RETRY HTTP {response.status_code}"
                    )
                    await asyncio.sleep(min(2 ** attempt, 30))
                    continue

                logger.error(
                    f"[{task.request_id}] {'TELEGRAM':<10} | HTTP {response.status_code}"
                )
                logger.error(response.text)
                break

            except Exception:
                logger.exception(
                    f"[{task.request_id}] {'WORKER':<10} | ERROR (attempt {attempt})"
                )
                await asyncio.sleep(min(2 ** attempt, 30))

        if not sent:
            logger.error(
                f"[{task.request_id}] {'TELEGRAM':<10} | FAILED AFTER {settings.TELEGRAM_MAX_RETRIES} ATTEMPTS"
            )

        telegram_queue.task_done()
        await asyncio.sleep(0.1)
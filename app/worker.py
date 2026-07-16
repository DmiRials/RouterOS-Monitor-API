import asyncio

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

        attempt = 1

        while True:

            try:

                response = await telegram.send(task.text)

                logger.info(
                    f"[{task.request_id}] {'TELEGRAM':<10} | HTTP {response.status_code} (attempt {attempt})"
                )

                #
                # Успешно
                #
                if response.status_code == 200:

                    logger.info(
                        f"[{task.request_id}] {'TELEGRAM':<10} | OK"
                    )

                    break

                #
                # Telegram просит подождать
                #
                if response.status_code == 429:

                    data = response.json()

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

                    attempt += 1

                    continue

                #
                # Любая другая ошибка
                #
                logger.error(
                    f"[{task.request_id}] {'TELEGRAM':<10} | HTTP {response.status_code}"
                )

                logger.error(response.text)

                break

            except Exception:

                logger.exception(
                    f"[{task.request_id}] {'WORKER':<10} | ERROR"
                )

                break

        telegram_queue.task_done()

        #
        # небольшая задержка между сообщениями
        #
        await asyncio.sleep(0.1)
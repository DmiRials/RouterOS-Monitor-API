import time
import uuid

from fastapi import APIRouter, HTTPException, Request

from app.auth import check_token
from app.formatter import format_message
from app.logger import logger
from app.models import StatusRequest
from app.queue import TelegramTask, telegram_queue

router = APIRouter()


@router.post("/status")
async def status(request: Request, data: StatusRequest):

    request_id = uuid.uuid4().hex[:8].upper()
    started = time.perf_counter()

    #
    # Логируем запрос
    #
    parts = [
        data.company,
        data.office,
        data.type,
        data.resource,
    ]

    parts = [x for x in parts if x]

    if data.message:
        event = "MESSAGE"
    elif data.status is True:
        event = "UP"
    elif data.status is False:
        event = "DOWN"
    else:
        event = "CUSTOM"

    logger.info(
        f"[{request_id}] {'REQUEST':<10} | "
        f"{request.client.host} | "
        f"{' | '.join(parts)} | "
        f"{event}"
    )

    #
    # Проверка токена
    #
    if not check_token(data.token):

        logger.warning(
            f"[{request_id}] {'AUTH':<10} | FAILED | "
            f"{request.client.host} | "
            f"token={data.token}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    logger.info(
        f"[{request_id}] {'AUTH':<10} | OK"
    )

    #
    # Для обычного мониторинга status обязателен.
    # Для произвольных сообщений допускается только message.
    #
    if data.status is None and not data.message:

        raise HTTPException(
            status_code=422,
            detail="status or message is required"
        )

    #
    # Формируем сообщение
    #
    text = format_message(data)

    logger.info(
        f"[{request_id}] {'MESSAGE':<10} | {text}"
    )

    #
    # Добавляем в очередь
    #
    await telegram_queue.put(
        TelegramTask(
            request_id=request_id,
            text=text
        )
    )

    logger.info(
        f"[{request_id}] {'QUEUE':<10} | ADDED"
    )

    elapsed = (time.perf_counter() - started) * 1000

    logger.info(
        f"[{request_id}] {'DONE':<10} | {elapsed:.1f} ms"
    )

    return {
        "success": True,
        "queued": True,
        "request_id": request_id
    }
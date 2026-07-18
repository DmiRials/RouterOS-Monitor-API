import time
import uuid
from asyncio import QueueFull

from fastapi import APIRouter, HTTPException, Request, Response

from app.auth import check_token
from app.cache import is_same_status, remember_status, status_cache_key
from app.formatter import format_message
from app.logger import logger
from app.models import StatusRequest
from app.queue import TelegramTask, telegram_queue

router = APIRouter()


@router.get("/")
async def root():
    return {
        "service": "Router Monitor API",
        "status": "ok",
        "endpoint": "/status"
    }


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@router.post("/status")
async def status(request: Request, data: StatusRequest):
    request_id = uuid.uuid4().hex[:8].upper()
    started = time.perf_counter()
    client_host = request.client.host if request.client else "unknown"

    if not check_token(data.token):
        logger.warning(
            f"[{request_id}] {'AUTH':<10} | FAILED | "
            f"{client_host}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

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
        f"{client_host} | "
        f"{' | '.join(parts)} | "
        f"{event}"
    )

    logger.info(
        f"[{request_id}] {'AUTH':<10} | OK"
    )

    if data.status is None and not data.message:
        raise HTTPException(
            status_code=422,
            detail="status or message is required"
        )

    if data.status is not None and not data.message:
        cache_key = status_cache_key(
            data.company,
            data.office,
            data.resource,
            data.server,
            data.type,
        )
        if is_same_status(cache_key, data.status):
            logger.info(
                f"[{request_id}] {'CACHE':<10} | SKIPPED DUPLICATE STATUS"
            )
            return {
                "accepted": True,
                "queued": False,
                "duplicate": True,
                "request_id": request_id
            }
    else:
        cache_key = None

    text = format_message(data)

    logger.info(
        f"[{request_id}] {'MESSAGE':<10} | {text}"
    )

    try:
        telegram_queue.put_nowait(
            TelegramTask(
                request_id=request_id,
                text=text
            )
        )
    except QueueFull:
        logger.error(
            f"[{request_id}] {'QUEUE':<10} | FULL"
        )
        raise HTTPException(
            status_code=503,
            detail="Telegram queue is full"
        )

    logger.info(
        f"[{request_id}] {'QUEUE':<10} | ADDED"
    )

    if cache_key is not None and data.status is not None:
        remember_status(cache_key, data.status)

    elapsed = (time.perf_counter() - started) * 1000

    logger.info(
        f"[{request_id}] {'DONE':<10} | {elapsed:.1f} ms"
    )

    return {
        "accepted": True,
        "queued": True,
        "request_id": request_id
    }

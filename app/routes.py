import time
from asyncio import QueueFull

from fastapi import APIRouter, HTTPException, Request, Response

from app.logger import logger
from app.models import StatusRequest
from app.services import EventService

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


@router.get("/health/live")
async def health_live():
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(request: Request):
    queue = request.app.state.queue
    return {"status": "ready", "queue_size": queue.qsize()}


@router.post("/status")
async def status(request: Request, data: StatusRequest):
    request_id = request.state.request_id
    started = time.perf_counter()
    client_host = request.client.host if request.client else "unknown"
    service: EventService = request.app.state.event_service

    try:
        result = service.accept(data, request_id)
    except PermissionError:
        logger.warning(
            f"[{request_id}] {'AUTH':<10} | FAILED | "
            f"{client_host}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
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
        f"[{request_id}] {'REQUEST':<10} | "
        f"{client_host} | "
        f"{data.company} | {data.office} | {data.type} | {data.resource}"
    )

    logger.info(
        f"[{request_id}] {'AUTH':<10} | OK"
    )

    if result.duplicate:
        logger.info(f"[{request_id}] {'CACHE':<10} | SKIPPED DUPLICATE STATUS")
    else:
        logger.info(f"[{request_id}] {'QUEUE':<10} | ADDED")

    elapsed = (time.perf_counter() - started) * 1000

    logger.info(
        f"[{request_id}] {'DONE':<10} | {elapsed:.1f} ms"
    )

    return {
        "accepted": True,
        "queued": result.queued,
        **({"duplicate": True} if result.duplicate else {}),
        "request_id": request_id
    }

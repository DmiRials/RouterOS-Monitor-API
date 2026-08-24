import asyncio
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import TokenRepository
from app.cache import StatusCache
from app.config import settings
from app.logger import logger
from app.queue import EventQueue
from app.routes import router
from app.services import EventService
from app.telegram import Telegram
from app.worker import telegram_worker


def request_id_for(request: Request) -> str:
    return getattr(request.state, "request_id", uuid.uuid4().hex[:8].upper())


@asynccontextmanager
async def lifespan(app: FastAPI):
    tokens = TokenRepository(settings.TOKENS_FILE)
    tokens.load()
    queue = EventQueue(settings.QUEUE_MAX_SIZE)
    telegram = Telegram()
    stop_event = asyncio.Event()

    app.state.queue = queue
    app.state.event_service = EventService(
        tokens=tokens,
        statuses=StatusCache(settings.STATUS_CACHE_MAX_SIZE),
        queue=queue,
    )
    worker = asyncio.create_task(telegram_worker(queue, telegram, stop_event))

    logger.info("=" * 70)
    logger.info("Router Monitor API v1.3")
    logger.info(f"Загружено API токенов: {len(tokens.tokens)}")
    logger.info("API запущено")
    logger.info("=" * 70)

    yield

    logger.info("Остановка API")
    try:
        await asyncio.wait_for(queue.join(), timeout=10)
    except asyncio.TimeoutError:
        logger.warning("WORKER     | Очередь не успела очиститься перед остановкой")

    stop_event.set()
    worker.cancel()
    try:
        await worker
    except asyncio.CancelledError:
        logger.info("WORKER     | Остановлен")

    await telegram.close()
    logger.info("TELEGRAM   | Клиент закрыт")


app = FastAPI(
    title="Router Monitor API",
    version="1.3",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex[:8].upper()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = request_id_for(request)
    logger.warning(
        f"[{request_id}] {'HTTP_ERROR':<10} | "
        f"{request.client.host if request.client else 'unknown'} | "
        f"{exc.status_code} | {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP error", "detail": exc.detail, "request_id": request_id},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = request_id_for(request)
    logger.warning(
        f"[{request_id}] {'VALIDATION':<10} | "
        f"{request.client.host if request.client else 'unknown'} | {exc.errors()}"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": jsonable_encoder(exc.errors()),
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = request_id_for(request)
    logger.exception(
        f"[{request_id}] {'UNHANDLED':<10} | "
        f"{request.client.host if request.client else 'unknown'} | {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "Unexpected server error. Check logs by request_id.",
            "request_id": request_id,
        },
    )


app.include_router(router)

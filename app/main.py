from contextlib import asynccontextmanager
import asyncio
import uuid

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.auth import TOKENS
from app.logger import logger
from app.queue import telegram_queue
from app.routes import router
from app.telegram import telegram
from app.worker import telegram_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 70)
    logger.info("Router Monitor API v1.2")
    logger.info(f"Загружено API токенов: {len(TOKENS)}")
    logger.info("Запуск Telegram Worker")
    worker = asyncio.create_task(
        telegram_worker()
    )
    logger.info("API запущено")
    logger.info("=" * 70)

    yield

    logger.info("=" * 70)
    logger.info("Остановка API")

    try:
        await asyncio.wait_for(telegram_queue.join(), timeout=10)
    except asyncio.TimeoutError:
        logger.warning("WORKER     | Очередь не успела очиститься перед остановкой")

    worker.cancel()

    try:
        await worker
    except asyncio.CancelledError:
        logger.info("WORKER     | Остановлен")

    await telegram.close()

    logger.info("TELEGRAM   | Клиент закрыт")
    logger.info("=" * 70)

app = FastAPI(
    title="Router Monitor API",
    version="1.2",
    lifespan=lifespan,

    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    request_id = uuid.uuid4().hex[:8].upper()
    logger.warning(
        f"[{request_id}] {'HTTP_ERROR':<10} | "
        f"{request.client.host if request.client else 'unknown'} | "
        f"{exc.status_code} | {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP error",
            "detail": exc.detail,
            "request_id": request_id
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    request_id = uuid.uuid4().hex[:8].upper()
    logger.warning(
        f"[{request_id}] {'VALIDATION':<10} | "
        f"{request.client.host if request.client else 'unknown'} | {exc.errors()}"
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": jsonable_encoder(exc.errors()),
            "request_id": request_id
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    request_id = uuid.uuid4().hex[:8].upper()
    logger.exception(
        f"[{request_id}] {'UNHANDLED':<10} | "
        f"{request.client.host if request.client else 'unknown'} | {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "Unexpected server error. Check logs by request_id.",
            "request_id": request_id
        },
    )


app.include_router(router)

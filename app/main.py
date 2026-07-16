from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI

from app.auth import TOKENS
from app.logger import logger
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

    #
    # Останавливаем Worker
    #
    worker.cancel()

    try:
        await worker
    except asyncio.CancelledError:
        logger.info("WORKER     | Остановлен")

    #
    # Закрываем HTTP клиент Telegram
    #
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

app.include_router(router)
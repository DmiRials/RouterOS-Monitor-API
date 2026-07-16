import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

LOG_DIR = Path(settings.LOG_DIR)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("RouterMonitor")

if not logger.handlers:

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s"
    )

    #
    # Консоль
    #
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    #
    # Файл
    #
    file = RotatingFileHandler(
        LOG_DIR / "api.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8"
    )

    file.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file)

    logger.propagate = False
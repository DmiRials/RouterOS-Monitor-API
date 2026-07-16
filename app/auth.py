from pathlib import Path

from app.config import settings
from app.logger import logger

TOKENS: set[str] = set()


def load_tokens() -> None:
    """
    Загрузка API токенов из файла.
    """

    TOKENS.clear()

    path = Path(settings.TOKENS_FILE)

    if not path.exists():
        logger.error(f"AUTH       | Файл не найден: {path}")
        return

    try:

        with path.open("r", encoding="utf-8") as file:

            for line in file:

                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                token = line.split("#", 1)[0].strip()

                if token:
                    TOKENS.add(token)

        logger.info(
            f"AUTH       | Загружено API токенов: {len(TOKENS)}"
        )

    except Exception:
        logger.exception(
            f"AUTH       | Ошибка чтения файла: {path}"
        )


def check_token(token: str) -> bool:
    """
    Проверка API токена.
    """

    return token in TOKENS


load_tokens()
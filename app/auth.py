from pathlib import Path

from app.config import settings
from app.logger import logger

TOKENS: set[str] = set()

def load_tokens() -> None:
    TOKENS.clear()
    path = Path(settings.TOKENS_FILE)
    if not path.exists():
        raise RuntimeError(f"Token file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                token = line.split("#", 1)[0].strip()
                if token:
                    TOKENS.add(token)

        if not TOKENS:
            raise RuntimeError(f"Token file has no active tokens: {path}")

        logger.info(
            f"AUTH       | Загружено API токенов: {len(TOKENS)}"
        )

    except Exception:
        logger.exception(
            f"AUTH       | Ошибка чтения файла токенов: {path}"
        )
        raise

def check_token(token: str) -> bool:
    return token in TOKENS


load_tokens()
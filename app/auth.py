from pathlib import Path
from secrets import compare_digest

from app.logger import logger

class TokenRepository:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.tokens: set[str] = set()

    def load(self) -> None:
        self.tokens.clear()
        path = self.path
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
                        self.tokens.add(token)

            if not self.tokens:
                raise RuntimeError(f"Token file has no active tokens: {path}")

            logger.info(
                f"AUTH       | Загружено API токенов: {len(self.tokens)}"
            )

        except Exception:
            logger.exception(
                f"AUTH       | Ошибка чтения файла токенов: {path}"
            )
            raise

    def check(self, token: str) -> bool:
        return any(compare_digest(token, known_token) for known_token in self.tokens)

import httpx

from app.config import settings

class Telegram:

    def __init__(self):
        self.url = (
            f"https://api.telegram.org/bot"
            f"{settings.BOT_TOKEN}/sendMessage"
        )
        self.client = self._create_client()

    def _create_client(self) -> httpx.AsyncClient:
        kwargs = {
            "timeout": settings.TELEGRAM_TIMEOUT
        }

        if settings.TELEGRAM_PROXY_ENABLED:
            if settings.TELEGRAM_PROXY_USER:
                proxy = (
                    f"{settings.TELEGRAM_PROXY_TYPE}://"
                    f"{settings.TELEGRAM_PROXY_USER}:"
                    f"{settings.TELEGRAM_PROXY_PASSWORD}@"
                    f"{settings.TELEGRAM_PROXY_HOST}:"
                    f"{settings.TELEGRAM_PROXY_PORT}"
                )

            else:
                proxy = (
                    f"{settings.TELEGRAM_PROXY_TYPE}://"
                    f"{settings.TELEGRAM_PROXY_HOST}:"
                    f"{settings.TELEGRAM_PROXY_PORT}"
                )

            kwargs["proxy"] = proxy

        return httpx.AsyncClient(**kwargs)

    async def send(self, text: str):
        payload = {
            "chat_id": settings.CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_notification": settings.TELEGRAM_SILENT
        }

        return await self.client.post(
            self.url,
            json=payload
        )

    async def close(self):
        await self.client.aclose()

telegram = Telegram()
from app.config import settings
from app.main import app

import uvicorn


if __name__ == "__main__":

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
    )
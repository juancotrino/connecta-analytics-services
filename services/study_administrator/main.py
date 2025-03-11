import os
import logging

import uvicorn
from fastapi import FastAPI

from utils.api_versions import add_api_versions
from app.core.logger import setup_logging


ENV = os.getenv("ENV", "local")

setup_logging()
logger = logging.getLogger(__name__)

# Initialize API
app = FastAPI()


@app.get("/check_health", tags=["Health"])
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}


add_api_versions(app)


if __name__ == "__main__":
    if ENV == "local":
        from dotenv import load_dotenv

        load_dotenv(".env")

    debug = ENV == "local"
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=debug)

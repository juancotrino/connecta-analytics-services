import os
import logging

import uvicorn
from fastapi import FastAPI, Query, HTTPException
from fastapi import status as http_status

from logger import setup_logging
import resources

ENV = os.getenv("ENV", "local")

setup_logging()

# Initialize API
app = FastAPI()

logger = logging.getLogger(__name__)


@app.get("/check_health")
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}


@app.get("/get_studies")
def get_studies(
    limit: int = 50,
    offset: int = 0,
    study_id: list[str] | None = Query(None),
    status: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    client: list[str] | None = Query(None),
    methodology: list[str] | None = Query(None),
    study_type: list[str] | None = Query(None),
):
    kwargs = {
        "study_id": study_id,
        "status": status,
        "country": country,
        "client": client,
        "methodology": methodology,
        "study_type": study_type,
    }

    try:
        studies = resources.get_studies(limit, offset, **kwargs)
    except Exception as e:
        message = f"Failed to fetch studies: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )

    return studies


if __name__ == "__main__":
    if ENV == "local":
        from dotenv import load_dotenv

        load_dotenv(".env")

    debug = ENV == "local"
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=debug)

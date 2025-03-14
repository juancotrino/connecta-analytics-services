from typing import TYPE_CHECKING
import os
from pathlib import Path
import json
import functools
import logging

from fastapi import HTTPException, status
from google.cloud import storage

logger = logging.getLogger(__name__)

# Initialize Google Cloud Storage client
storage_client = storage.Client()

if TYPE_CHECKING:
    from fastapi import Request

ENV = os.getenv("ENV", "local")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if ENV == "local":
    parent_folder = Path(__file__).parent
    service_name = f"service-{parent_folder}"
else:
    service_name = os.getenv("K_SERVICE")

BUCKET_NAME = f"{GCP_PROJECT_ID}-{service_name}"


def get_event_data(request: "Request"):
    return {header.split("-")[-1]: value for header, value in request.headers.items()}


def eventarc_file_downloader(func):
    """
    Decorator to extract the file name from an Eventarc event, download it from Cloud Storage,
    and pass it to the endpoint function.
    """

    @functools.wraps(func)
    async def wrapper(request: "Request", *args, **kwargs):
        try:
            logger.info("Enters triggered endpoint")
            event_data = get_event_data(request)
            logger.info("Event data:", event_data)
            logger.info("Request json:", request.json())
            logger.info("Request body:", request.body())
            subject = event_data.get("subject")
            logger.info("Subject:", subject)
            # Parse the Eventarc request
            body = await request.json()
            event_data = body.get("message", {}).get("data", "{}")
            event_data = json.loads(event_data)  # Decode the base64 message data

            # Extract file name
            file_name = event_data.get("name")
            if not file_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File name not found in event",
                )

            # Download file from Cloud Storage
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(file_name)
            file_content = blob.download_as_bytes()

            # Call the actual processing function with the file content
            return await func(file_name, file_content, *args, **kwargs)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    return wrapper

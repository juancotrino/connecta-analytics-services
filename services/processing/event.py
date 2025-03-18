from typing import TYPE_CHECKING
import os
from pathlib import Path
from functools import wraps
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
    parent_folder = Path(__file__).parent.name
    service_name = f"service-{parent_folder}"
else:
    service_name = os.getenv("K_SERVICE")

BUCKET_NAME = f"{GCP_PROJECT_ID}-{service_name}"


def get_file_name(request_headers: dict[str, str]):
    event_data = {
        header.split("-")[-1]: value for header, value in request_headers.items()
    }
    return "/".join(event_data.get("subject").split("/")[1:])


def download_blob(file_name: str):
    # Download file from Cloud Storage
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    return blob.download_as_bytes()


def eventarc_file_downloader(func):
    """
    Decorator to extract the file name from an Eventarc event, download it from Cloud Storage,
    and pass it to the endpoint function.
    """

    @wraps(func)
    async def wrapper(request: "Request", file_name, file_content, *args, **kwargs):
        try:
            # Extract file name
            file_name = get_file_name(request.headers)
            if not file_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File name not found in event",
                )

            # Download file from Cloud Storage
            file_content = download_blob(file_name)

            # Call the actual processing function with the file content
            return await func(request, file_name, file_content, *args, **kwargs)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    return wrapper

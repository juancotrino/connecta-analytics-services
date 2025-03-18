from typing import TYPE_CHECKING
import os
import logging
from pathlib import Path
import yaml
import json

from starlette.datastructures import UploadFile

if TYPE_CHECKING:
    from google.cloud.storage import Bucket

from google.cloud import storage

logger = logging.getLogger(__name__)


ENV = os.getenv("ENV", "local")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

parent_folder = Path(__file__).parent

with open(f"{parent_folder}/allowed_file_types.yaml", "r") as file:
    allowed_file_types = yaml.safe_load(file)

# Initialize Google Cloud Storage client
storage_client = storage.Client()


def get_service_bucket(service_name: str):
    BUCKET_NAME = f"{GCP_PROJECT_ID}-service-{service_name}"
    return storage_client.bucket(BUCKET_NAME)


def get_service_allowed_file_types(service_name: str):
    return tuple(allowed_file_types["services"].get(service_name, []))


def parse_metadata(file_uuid: str, metadata: str):
    """Parses metadata from form-data input"""
    try:
        return json.loads(metadata)
    except Exception as e:
        logger.warning(
            f"Metadata for file uuid '{file_uuid}' could not be parsed. Error: {e}"
        )
        return None


def generate_blob(
    file_uuid: str,
    original_file_name: str,
    data: UploadFile | str,
    bucket: "Bucket",
    bucket_folder: str,
    suffix: str | None = "",
    new_file_extension: str | None = None,
):
    if isinstance(data, UploadFile):
        file_extension = data.filename.split(".")[-1]
    else:
        file_extension = "json"

    new_file_name = (
        f"{file_uuid}{suffix}."
        f"{file_extension if not new_file_extension else new_file_extension}"
    )

    # Upload main file
    blob = bucket.blob(f"{bucket_folder}/{new_file_name}")

    # Set metadata (original file name)
    blob.metadata = {"original_file_name": original_file_name}

    if isinstance(data, UploadFile):
        blob.upload_from_file(data.file, content_type=data.content_type)
    else:
        blob.upload_from_string(json.dumps(data), content_type="application/json")

    return blob

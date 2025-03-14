import os
import uuid
import logging

import uvicorn
from fastapi import FastAPI, UploadFile, Form, File, status
from fastapi.exceptions import HTTPException

from logger import setup_logging
import resources

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


@app.post("/upload_file", tags=["File management"])
async def upload_file(
    service_name: str,
    bucket_folder: str = "landingzone",
    metadata: str | None = Form(...),
    file: UploadFile = File(...),
):
    """
    Receives a file from the frontend and uploads it to Google Cloud Storage.
    Returns the public URL or metadata of the uploaded file.
    """
    # Ensure the file has a valid name and is an xlsx file

    allowed_file_types = resources.get_service_allowed_file_types(service_name)

    if not allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The service do not exist or currently do not support any type of file."
            ),
        )

    if not file.filename.endswith(allowed_file_types):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid file type. Only {', '.join(allowed_file_types)} "
                "file types are allowed."
            ),
        )

    try:
        bucket = resources.get_service_bucket(service_name)

        file_uuid = str(uuid.uuid4())
        file_blob = resources.generate_blob(
            file_uuid, file.filename, file, bucket, bucket_folder
        )

        response_data = {
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "file_uuid": file_uuid,
            "file_url": file_blob.public_url,
        }

        try:
            metadata = resources.parse_metadata(file_uuid, metadata)
            # Upload metadata file (if provided or parsed correctly)
            if metadata:
                metadata_blob = resources.generate_blob(
                    file_uuid,
                    file.filename,
                    metadata,
                    bucket,
                    bucket_folder,
                    suffix="_metadata",
                    new_file_extension="json",
                )
                response_data["metadata_url"] = metadata_blob.public_url
        except Exception as e:
            logger.warning(
                f"Invalid metadata format for file uuid '{file_uuid}': {str(e)}"
            )

        return response_data

    except Exception as e:
        logger.error(f"An error uploading the blob occurred: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


if __name__ == "__main__":
    ENV = os.getenv("ENV", "local")

    if ENV == "local":
        from dotenv import load_dotenv

        load_dotenv(".env")

    debug = ENV == "local"
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=debug)

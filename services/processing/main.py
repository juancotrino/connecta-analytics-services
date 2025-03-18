import os
import shutil
import logging
import tempfile

import uvicorn
from fastapi import FastAPI, status, Request
from fastapi.exceptions import HTTPException

from logger import setup_logging
from event import eventarc_file_downloader
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


@app.post("/get_from_storage", tags=["File processor"])
@eventarc_file_downloader
def get_from_storage(
    request: Request, file_name: str | None = None, file_content: bytes | None = None
):
    # Check if the file is inside the correct folder
    if not file_name.startswith("landingzone/"):
        logger.info(
            f"The file was NOT loaded into the /landingzone folder: {file_name}"
        )
        return {"message": "Ignored, file not in target folder"}

    # Process the file upload
    logger.info(f"Processing file: {file_name}")

    return {"message": file_name}


@app.post("/statistical_processing", tags=["Processing"])
def statistical_processing(file):
    # NOTE: This should receive the fileid of the file loaded to cloud storage
    # landingzone by the storage_proxy service

    # Ensure the file has a valid name and is an xlsx file
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .xlsx files are allowed.",
        )

    # Create a temporary file path
    temp_dir = tempfile.gettempdir()
    temp_filename = f"temp_{os.getpid()}_{file.filename}"  # Avoid filename collisions
    temp_input_path = os.path.join(temp_dir, temp_filename)

    try:
        # Save the uploaded file temporarily
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        temp_output_path = resources.calculate_statistical_significance(temp_input_path)
        logger.info(
            f"Statistical significance for file '{file.filename}' "
            "calculated successfully."
        )
        # TODO: Load file to cloud storage
        return {"message": "File uploaded successfully", "path": temp_input_path}

    except Exception as e:
        message = f"Error calculating statistical significance: {str(e)}"
        logger.error(message)
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )

    finally:
        file.file.close()
        os.remove(temp_input_path)
        # Clean up temporary files
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)


if __name__ == "__main__":
    ENV = os.getenv("ENV", "local")

    if ENV == "local":
        from dotenv import load_dotenv

        load_dotenv(".env")

    debug = ENV == "local"
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=debug)

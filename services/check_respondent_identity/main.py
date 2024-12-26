import os

from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
import uvicorn

from twilio.rest import Client as TwilioClient

from logger import setup_logging, get_logger


setup_logging()
logger = get_logger(__name__)

app = FastAPI()

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)


@app.post("/send_code/{phone_number}")
async def send_code(phone_number: str):
    """
    Send an SMS verification code to the given phone number.
    """
    if not phone_number:
        message = "Phone number is required."
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    try:
        # Use Twilio to send the verification SMS
        verification = twilio_client.verify.services(
            os.getenv("TWILIO_SERVICE_SID")
        ).verifications.create(
            to=phone_number,
            channel='sms'
        )
        _status = verification.status
        message = f"Verification code sent with status {_status}."
        logger.info(message)
        return {"message": message}

    except Exception as e:
        message = f"Failed to send code: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )

@app.post("/verify/{phone_number}/{code}")
async def verify(phone_number: str, code: str):
    """
    Verify the code sent to the phone number.
    """
    if not phone_number or not code:
        message = "Phone number and code are required."
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    try:
        # Verify the code using Twilio
        verification_check = twilio_client.verify.services(
            os.getenv("TWILIO_SERVICE_SID")
        ).verification_checks.create(
            to=phone_number,
            code=code
        )
        _status = verification_check.status
        message = f"Verification code sent with status {_status}."
        logger.info(message)
        return {"message": message}

    except Exception as e:
        message = f"Verification failed: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)

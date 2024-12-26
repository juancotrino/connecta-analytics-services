import os

from flask import Flask
from twilio.rest import Client as TwilioClient

from logger import setup_logging
import resources


setup_logging()

app = Flask(__name__)

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)


@app.route("/check_health")
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}, 200


@app.route("/send_code/<path:phone_number>")
def send_code(phone_number: str):
    """
    Send an SMS verification code to the given phone number.
    """
    if not phone_number:
        message = "Phone number is required."
        app.logger.error(message)
        return {"message": message}, 400

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
        app.logger.info(message)
        return {"message": message}, 200

    except Exception as e:
        message = f"Failed to send code: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


@app.route("/verify/<path:phone_number>/<path:code>")
def verify(phone_number: str, code: str):
    """
    Verify the code sent to the phone number.
    """
    if not phone_number or not code:
        message = "Phone number and code are required."
        app.logger.error(message)
        return {"message": message}, 400

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
        app.logger.info(message)
        return {"message": message}, 200

    except Exception as e:
        message = f"Verification failed: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)

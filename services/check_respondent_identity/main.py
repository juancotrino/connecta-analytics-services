import os
from datetime import datetime, timezone

from flask import Flask, request
from flask_cors import CORS

from logger import setup_logging
import resources

ENV = os.getenv("ENV", "local")

if ENV == "local":
    from dotenv import load_dotenv

    load_dotenv("../../.env")

setup_logging()

app = Flask(__name__)

ALLOWED_ORIGIN = "https://connecta.questionpro.com"  # Replace with the allowed origin

# Configure CORS to allow only specific origin
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGIN}})


@app.route("/check_health")
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}, 200


@app.route(
    "/check_respondent_qualified/<path:country>/<path:phone_number>/<path:project_type>"
)
def check_respondent_qualified(country: str, phone_number: str, project_type: str):
    """
    Check if the respondent is qualified to take the survey.
    """
    if not phone_number:
        message = "Phone number is required."
        app.logger.error(message)
        return {"message": message}, 400

    try:
        phone_number = int(resources.transform_phone_number(country, phone_number))
        project_type = project_type.strip().lower()
        # Check if the respondent is qualified
        is_qualified = resources.is_respondent_qualified(phone_number, project_type)

        if is_qualified:
            message = (
                f"Respondent is qualified. Phone number "
                f"{phone_number} and project type {project_type}."
            )
        else:
            message = (
                f"Respondent is not qualified. Phone number "
                f"{phone_number} and project type {project_type}."
            )

        app.logger.info(message)
        return {
            "message": message,
            "is_qualified": is_qualified,
        }, 200 if is_qualified else 403

    except Exception as e:
        message = f"Failed to check respondent qualification: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


@app.route("/send_code/<path:country>/<path:phone_number>")
def send_code(country: str, phone_number: str):
    """
    Send an SMS verification code to the given phone number.
    """
    if not phone_number:
        message = "Phone number is required."
        app.logger.error(message)
        return {"message": message}, 400

    try:
        # Sanitize the phone number
        phone_number = f"+{resources.transform_phone_number(country, phone_number)}"
        # Use Twilio to send the verification SMS
        verification = resources.send_code(phone_number)
        _status = verification.status
        message = f"Verification code sent with status '{_status}'."
        app.logger.info(message)
        return {"message": message, "status": _status}, 200

    except Exception as e:
        message = f"Failed to send code: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


@app.route("/verify/<path:country>/<path:phone_number>/<path:code>")
def verify(country: str, phone_number: str, code: str):
    """
    Verify the code sent to the phone number.
    """
    if not phone_number or not code:
        message = "Phone number and code are required."
        app.logger.error(message)
        return {"message": message}, 400

    try:
        # Sanitize the phone number
        phone_number = f"+{resources.transform_phone_number(country, phone_number)}"
        # Sanitize the code
        code = code.replace(" ", "")
        # Verify the code using Twilio
        verification_check = resources.verify_code(phone_number, code)
        _status = verification_check.status
        message = f"Verification code sent with status '{_status}'."
        app.logger.info(message)
        return {
            "message": message,
            "status": _status,
        }, 200 if _status == "approved" else 400

    except Exception as e:
        message = f"Verification failed: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


@app.route("/write_respondent", methods=["POST"])
def write_respondent():
    """
    Verify the code sent to the phone number.
    """
    country = request.get_json().get("country").strip()
    phone_number = int(
        resources.transform_phone_number(
            country, request.get_json().get("phone_number")
        )
    )

    data = {
        "country": country,
        "phone_number": phone_number,
        "name": request.get_json().get("name").strip().lower(),
        "age": int(request.get_json().get("age").strip()),
        "gender": request.get_json().get("gender").strip().lower(),
        "project_type": request.get_json().get("project_type").strip().lower(),
        "response_datetime": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    app.logger.info("Data dictionary builded")

    try:
        # Writes to BQ
        resources.write_to_bq(data)
        message = "Respondent data saved successfully."
        app.logger.info(message)
        return {"message": message}, 200

    except Exception as e:
        message = f"Error writing respondent data to BQ: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


if __name__ == "__main__":
    debug = ENV == "local"
    app.run(debug=debug, host="0.0.0.0", port=8080)

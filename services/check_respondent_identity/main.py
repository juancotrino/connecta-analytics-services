from datetime import datetime

from flask import Flask, request

from logger import setup_logging
import resources


setup_logging()

app = Flask(__name__)


@app.route("/check_health")
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}, 200


@app.route("/check_respondent_qualified/<path:phone_number>/<path:study_type>")
def check_respondent_qualified(phone_number: str, study_type: str):
    """
    Check if the respondent is qualified to take the survey.
    """
    if not phone_number:
        message = "Phone number is required."
        app.logger.error(message)
        return {"message": message}, 400

    try:
        # Check if the respondent is qualified
        is_qualified = resources.is_respondent_qualified(
            phone_number, study_type
        )

        if is_qualified:
            message = (
                f"Respondent is qualified. Phone number "
                f"{phone_number} and study type {study_type}."
            )
        else:
            message = (
                f"Respondent is not qualified. Phone number "
                f"{phone_number} and study type {study_type}."
            )

        app.logger.info(message)
        return {
            "message": message,
            "is_qualified": is_qualified
        }, 200 if is_qualified else 403

    except Exception as e:
        message = f"Failed to check respondent qualification: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


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
        verification = resources.send_code(phone_number)
        _status = verification.status
        message = f"Verification code sent with status '{_status}'."
        app.logger.info(message)
        return {
            "message": message,
            "status": _status
        }, 200

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
        verification_check = resources.verify_code(phone_number, code)
        _status = verification_check.status
        message = f"Verification code sent with status '{_status}'."
        app.logger.info(message)
        return {
            "message": message,
            "status": _status
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
    data = {
        "name": request.args.get("name"),
        "last_name": request.args.get("last_name"),
        "phone_number": request.args.get("phone_number"),
        "age": request.args.get("age"),
        "project_type": request.args.get("project_type"),
        "response_datetime": datetime.now()
    }

    try:
        # Writes to BQ
        resources.write_to_bq(data)
        message = f"Respondent data saved successfully."
        app.logger.info(message)
        return {"message": message}, 200

    except Exception as e:
        message = f"Verification failed: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)

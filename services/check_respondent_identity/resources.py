import os

from twilio.rest import Client as TwilioClient

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

def send_code(phone_number: str):
    return twilio_client.verify.services(
        os.getenv("TWILIO_SERVICE_SID")
    ).verifications.create(
        to=phone_number,
        channel='sms'
    )

def verify_code(phone_number: str, code: str):
    return twilio_client.verify.services(
        os.getenv("TWILIO_SERVICE_SID")
    ).verification_checks.create(
        to=phone_number,
        code=code
    )

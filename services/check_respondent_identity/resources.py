from dataclasses import dataclass
import os
import random
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json

from twilio.rest import Client as TwilioClient

from google.cloud import bigquery
from google.cloud import firestore


BQ_DATASET = "survey_history"
BQ_TABLE = "respondent"

CODE_EXPIRY_MINUTES = 5
MAX_REQUESTS_PER_HOUR = 3

FIRESTORE_PHONE_VERIFICATION_COLLECTION = "phone_verification"

WHATSAPP_TEMPLATE_NAME = "survey_verification_code"

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
)

verify_service = twilio_client.verify.services(os.getenv("TWILIO_SERVICE_SID"))

bq_client = bigquery.Client()
db = firestore.Client()

with open(Path(__file__).parent.joinpath("countries_phone_codes.json"), "r") as file:
    countries_phone_codes = json.load(file)


def get_country_phone_code(country_code: str):
    return countries_phone_codes.get(country_code)


def transform_phone_number(country: str, phone_number: str):
    phone_number = phone_number.replace("+", "").replace(" ", "")
    country_phone_code = get_country_phone_code(country)
    # Check if the phone number already has the country code
    if country_phone_code in phone_number[: len(country_phone_code)]:
        country_phone_code = ""

    return f"{country_phone_code}{phone_number}"


def get_respondent_data(phone_number: int, project_type: str):
    # Define your query to check for existing records
    query = """
        SELECT
            response_datetime
        FROM `{project_id}.{dataset}.{table}`
        WHERE phone_number = @phone_number
            AND project_type = @project_type
    """

    # Define the query parameters
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("phone_number", "INT64", phone_number),
            bigquery.ScalarQueryParameter("project_type", "STRING", project_type),
        ]
    )

    # Execute the query
    formatted_query = query.format(
        project_id=os.getenv("GCP_PROJECT_ID"),
        dataset=BQ_DATASET,
        table=BQ_TABLE,
    )
    query_job = bq_client.query(formatted_query, job_config=job_config)

    # Fetch results
    return list(query_job.result())


def is_respondent_qualified(phone_number: int, project_type: str):
    # Fetch results
    results = get_respondent_data(phone_number, project_type)

    if len(results) > 1:
        return False

    if not results:
        return True

    result = results[0].response_datetime.replace(tzinfo=timezone.utc)

    if (datetime.now(timezone.utc) - result).days < 180:
        return False

    return True


def send_code(phone_number: str):
    return verify_service.verifications.create(to=phone_number, channel="sms")


def verify_code(phone_number: str, code: str):
    return verify_service.verification_checks.create(to=phone_number, code=code)


def write_to_bq(data: dict):
    # Fetch results
    results = get_respondent_data(data["phone_number"], data["project_type"])

    if len(results) == 0:
        # No record found, insert new data
        job = bq_client.load_table_from_json(
            [data], (f"{os.getenv('GCP_PROJECT_ID')}.{BQ_DATASET}.{BQ_TABLE}")
        )
        job.result()  # Wait for the job to complete

    elif len(results) == 1:
        # One record found, update the response_datetime
        update_query = """
            UPDATE `{project_id}.{dataset}.{table}`
            SET response_datetime = @response_datetime
            WHERE phone_number = @phone_number
                AND project_type = @project_type
        """
        update_job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "response_datetime", "DATETIME", datetime.now(timezone.utc)
                ),
                bigquery.ScalarQueryParameter(
                    "phone_number", "INT64", data["phone_number"]
                ),
                bigquery.ScalarQueryParameter(
                    "project_type", "STRING", data["project_type"]
                ),
            ]
        )
        formatted_update_query = update_query.format(
            project_id=os.getenv("GCP_PROJECT_ID"),
            dataset=BQ_DATASET,
            table=BQ_TABLE,
        )
        update_query_job = bq_client.query(
            formatted_update_query, job_config=update_job_config
        )
        update_query_job.result()  # Wait for the job to complete

    else:
        raise ValueError(
            "Multiple records found for the given phone number and project type"
        )


def store_wp_code(phone_number: str, code: int):
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=CODE_EXPIRY_MINUTES)
    doc_ref = db.collection(FIRESTORE_PHONE_VERIFICATION_COLLECTION).document(
        phone_number
    )

    @firestore.transactional
    def transaction_operation(transaction, doc_ref):
        snapshot = doc_ref.get(transaction=transaction)

        if snapshot.exists:
            data = snapshot.to_dict()
            last_request = data.get("last_request")
            request_count = data.get("request_count", 0)

            # Reset count if more than an hour passed
            if last_request and (now - last_request).total_seconds() > 3600:
                request_count = 0

            if request_count >= MAX_REQUESTS_PER_HOUR:
                raise Exception("Rate limit exceeded")

            request_count += 1

            transaction.update(
                doc_ref,
                {
                    "code": code,
                    "expires_at": expires_at,
                    "last_request": firestore.SERVER_TIMESTAMP,
                    "request_count": request_count,
                },
            )

        else:
            # First time: create document
            transaction.set(
                doc_ref,
                {
                    "code": code,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "last_request": firestore.SERVER_TIMESTAMP,
                    "expires_at": expires_at,
                    "request_count": 1,
                },
            )

    transaction = db.transaction()
    try:
        transaction_operation(transaction, doc_ref)
    except Exception as e:
        raise e


def send_wp_code(phone_number: str) -> dict:
    random_code = random.randint(1000, 9999)
    store_wp_code(phone_number, random_code)
    response = requests.post(
        f"https://graph.facebook.com/v23.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages",
        headers={
            "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
            "Content-Type": "application/json",
        },
        json={
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "template",
            "template": {
                "name": WHATSAPP_TEMPLATE_NAME,
                "language": {"code": "es_CO"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": str(random_code)}],
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": str(random_code)}],
                    },
                ],
            },
        },
    )
    return response.json()


@dataclass
class WPCodeVerification:
    verified: bool
    status: str


def verify_wp_code(phone_number: str, code: str) -> WPCodeVerification:
    doc = (
        db.collection(FIRESTORE_PHONE_VERIFICATION_COLLECTION)
        .document(phone_number)
        .get()
    )

    info = doc.to_dict()

    if info["expires_at"] < datetime.now(timezone.utc):
        doc.reference.delete()
        return WPCodeVerification(verified=False, status="code_expired")

    if str(info["code"]) != str(code):
        return WPCodeVerification(verified=False, status="invalid_code")

    # Verified — delete record
    doc.reference.delete()
    return WPCodeVerification(verified=True, status="success")

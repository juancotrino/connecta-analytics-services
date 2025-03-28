import os
from pathlib import Path
from datetime import datetime, timezone
import json

from twilio.rest import Client as TwilioClient

from google.cloud import bigquery

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
)

bq_client = bigquery.Client()

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


def get_respondent_date(phone_number: int, project_type: str):
    # Define your query to check for existing records
    query = """
        SELECT
            response_datetime
        FROM `{project_id}.survey_history.respondent`
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
    formatted_query = query.format(project_id=os.getenv("GCP_PROJECT_ID"))
    query_job = bq_client.query(formatted_query, job_config=job_config)

    # Fetch results
    return list(query_job.result())


def is_respondent_qualified(phone_number: int, project_type: str):
    # Fetch results
    results = get_respondent_date(phone_number, project_type)

    if len(results) > 1:
        return False

    if not results:
        return True

    result = results[0].response_datetime.replace(tzinfo=timezone.utc)

    if (datetime.now(timezone.utc) - result).days < 180:
        return False

    return True


def send_code(phone_number: str):
    return twilio_client.verify.services(
        os.getenv("TWILIO_SERVICE_SID")
    ).verifications.create(to=phone_number, channel="sms")


def verify_code(phone_number: str, code: str):
    return twilio_client.verify.services(
        os.getenv("TWILIO_SERVICE_SID")
    ).verification_checks.create(to=phone_number, code=code)


def write_to_bq(data: dict):
    # Fetch results
    results = get_respondent_date(data["phone_number"], data["project_type"])

    if len(results) == 0:
        # No record found, insert new data
        job = bq_client.load_table_from_json(
            [data], (f"{os.getenv('GCP_PROJECT_ID')}.survey_history.respondent")
        )
        job.result()  # Wait for the job to complete

    elif len(results) == 1:
        # One record found, update the response_datetime
        update_query = """
            UPDATE `{project_id}.survey_history.respondent`
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
            project_id=os.getenv("GCP_PROJECT_ID")
        )
        update_query_job = bq_client.query(
            formatted_update_query, job_config=update_job_config
        )
        update_query_job.result()  # Wait for the job to complete

    else:
        raise ValueError(
            "Multiple records found for the given phone number and project type"
        )

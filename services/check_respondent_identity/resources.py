import os
from datetime import datetime
from dateutil.parser import parse

from twilio.rest import Client as TwilioClient

from google.cloud import bigquery

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

bq_client = bigquery.Client()

def is_respondent_qualified(phone_number: str, study_type: str):

    # Define your query
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
            bigquery.ScalarQueryParameter(
                "phone_number", "STRING", phone_number
            ),
            bigquery.ScalarQueryParameter(
                "project_type", "STRING", study_type
            ),
        ]
    )

    # Execute the query
    formatted_query = query.format(project_id=os.getenv("GCP_PROJECT_ID"))
    query_job = bq_client.query(formatted_query, job_config=job_config)

    # Fetch results
    results = query_job.result()

    if len(results) > 1:
        return False

    result = parse(results[0].response_datetime)
    if (datetime.now() - result).days < 180:
        return False

    return True

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

def write_respondent(data: dict):
    # Write the respondent data to the database
    job = bq_client.load_table_from_json(
        data, (
            f'{os.getenv("GCP_PROJECT_ID")}'
            f'.survey_history'
            f'.respondent'
        )
    )
    job.result()  # Wait for the job to complete

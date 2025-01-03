import os

from flask import Flask

from logger import setup_logging

ENV = os.getenv("ENV", "local")

if ENV == "local":
    from dotenv import load_dotenv

    load_dotenv('../../.env')

setup_logging()

app = Flask(__name__)


@app.route("/check_health")
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}, 200

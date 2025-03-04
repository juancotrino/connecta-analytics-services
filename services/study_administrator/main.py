import os

from flask import Flask, request

from logger import setup_logging
import resources

ENV = os.getenv("ENV", "local")

if ENV == "local":
    from dotenv import load_dotenv

    load_dotenv("../../.env")

setup_logging()

app = Flask(__name__)


@app.route("/check_health")
def check_health():
    """
    Check the health of the service.
    """
    return {"message": "Service is healthy."}, 200


@app.route("/get_studies", methods=["GET"])
def get_studies():
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    kwargs = {
        "study_id": request.args.getlist("study_id"),
        "status": request.args.getlist("status"),
        "country": request.args.getlist("country"),
        "client": request.args.getlist("client"),
        "methodology": request.args.getlist("methodology"),
        "study_type": request.args.getlist("study_type"),
    }

    try:
        studies = resources.get_studies(limit, offset, **kwargs)
    except Exception as e:
        message = f"Failed to fetch studies: {str(e)}"
        app.logger.error(message)
        return {"message": message}, 500

    return studies, 200


if __name__ == "__main__":
    debug = ENV == "local"
    app.run(debug=debug, host="0.0.0.0", port=8080)

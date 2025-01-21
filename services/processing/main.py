import os

from flask import Flask, request, send_file

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


@app.route("/statistical_processing", methods=["POST"])
def statistical_processing():
    # Ensure a file was uploaded
    if "file" not in request.files:
        return {"error": "No file part"}, 400

    uploaded_file = request.files["file"]

    # Ensure the file has a valid name and is an xlsx file
    if uploaded_file.filename == "":
        return {"error": "No selected file"}, 400
    if not uploaded_file.filename.endswith(".xlsx"):
        return {"error": "Invalid file type. Only .xlsx files are allowed."}, 400

    temp_input_path = None
    temp_output_path = None

    try:
        # Save the uploaded file temporarily
        temp_input_path = os.path.join("temp", uploaded_file.filename)
        os.makedirs(os.path.dirname(temp_input_path), exist_ok=True)
        uploaded_file.save(temp_input_path)

        temp_output_path = resources.calculate_statistical_significance(temp_input_path)

        # Return the processed file
        return send_file(temp_output_path, as_attachment=True)

    except Exception as e:
        message = f"Error calculating statistical significance: {str(e)}"
        app.logger.error(message)
        app.logger.exception(e)
        return {"message": message}, 500

    finally:
        # Clean up temporary files
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)


if __name__ == "__main__":
    debug = ENV == "local"
    app.run(debug=debug, host="0.0.0.0", port=8081)

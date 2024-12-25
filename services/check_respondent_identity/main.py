from flask import Flask, request

from logger import setup_logging
import resources


setup_logging()

app = Flask(__name__)

@app.route("/")
def check_respondent_identity():
    try:
        phone_number = request.args.get('phone_number')

        if phone_number is None:
            message = "Phone number is required"
            app.logger.info(message)
            return {"message": message}, 400

        message = (
            f"Phone number provided: {phone_number}. "
            f"resources test: {resources.test_resource()}"
        )
        return {"message": message}, 200

    except Exception as e:
        # Create the failed response
        message = str(e)
        app.logger.error(message)
        return {"message": message}, 400


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)

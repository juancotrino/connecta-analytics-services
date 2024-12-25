# from goblet import Goblet, goblet_entrypoint
# from flask import Request

# import resources

# app = Goblet(function_name="check_respondent_identity")
# goblet_entrypoint(app)


# @app.route('/check_respondent_identity', methods=['GET'])
# def check_respondent_identity(request: Request):
#     try:
#         return {"hello": "world"}, 200
#         # phone_number = request.args.get('phone_number')

#         # if phone_number is None:
#         #     message = "Phone number is required"
#         #     app.log.info(message)
#         #     return {"message": message}, 400

#         # message = f"Phone number provided: {phone_number}. "
#         # f"resources test: {resources.test_resource()}"
#         # return {"message": message}, 200

#     except Exception as e:
#         # Create the failed response
#         message = str(e)
#         app.log.error(message)
#         return {"message": message}, 400

import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

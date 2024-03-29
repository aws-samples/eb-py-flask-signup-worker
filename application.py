# Copyright 2013. Amazon Web Services, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging

import boto3
import flask
from flask import Response, request

# Create and configure the Flask app
application = flask.Flask(__name__)
application.config.from_object("default_config")
application.debug = application.config["FLASK_DEBUG"] in ["true", "True"]

# Email message vars
SUBJECT = "Thanks for signing up!"
BODY = "Hi %s!\n\nWe're excited that you're excited about our new product! We'll let you know as soon as it's available.\n\nThanks,\n\nA New Startup"
CHARSET = "UTF-8"


@application.route("/customer-registered", methods=["POST"])
def customer_registered():
    """Send an e-mail using SES"""

    response = None
    if request.json is None:
        # Expect application/json request
        response = Response("", status=415)
    else:
        request_content = json.loads(request.data)
        message = dict()
        try:
            # If the message has an SNS envelope, extract the inner message
            if request_content["TopicArn"] and request_content["Message"]:
                message = json.loads(request_content["Message"])
            else:
                message = request_content

            # Connect to SES and send an e-mail
            ses = boto3.client("ses", application.config["AWS_REGION"])
            ses.send_email(
                Destination={
                    "ToAddresses": [
                        message["email"],
                    ],
                },
                Message={
                    "Body": {
                        "Text": {
                            "Charset": CHARSET,
                            "Data": BODY % (message["name"]),
                        },
                    },
                    "Subject": {
                        "Charset": CHARSET,
                        "Data": SUBJECT,
                    },
                },
                Source=application.config["SOURCE_EMAIL_ADDRESS"],
            )
            response = Response("", status=200)
        except Exception as ex:
            logging.exception("Error processing message: %s" % request.json)
            response = Response(ex.message, status=500)

    return response


@application.route("/")
def print_hello():
    response = Response("Hello", status=200)
    return response


if __name__ == "__main__":
    application.run(host="0.0.0.0")

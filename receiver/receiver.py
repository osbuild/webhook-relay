#!/usr/bin/env python
import os
import hmac
import hashlib
import json

import boto3
from flask import Flask, request, abort

app = Flask(__name__)

GITHUB_SECRET = os.environ["GITHUB_SECRET"]
SQS_QUEUE = os.environ['SQS_QUEUE']
SQS_REGION = os.environ['SQS_REGION']


@app.route("/github-webhook", methods=['POST'])
def github_webhook_endpoint():
    """Endpoint for a GitHub webhook"""

    # Populate the data that was sent so the hmac check is ok.
    request.get_data()

    # Extract signature header
    signature = request.headers.get("X-Hub-Signature")
    if not signature or not signature.startswith("sha1="):
        abort(400, "X-Hub-Signature required")

    # Create local hash of payload
    digest = hmac.new(
        GITHUB_SECRET.encode(),
        request.data,
        hashlib.sha1
    ).hexdigest()

    if not hmac.compare_digest(signature, "sha1=" + digest):
        abort(400, "Invalid signature")

    # Create a big dictionary with headers and payload.
    message = {
        'headers': dict(request.headers),
        'payload': json.loads(request.form.get('payload'))
    }

    # Send the message to Amazon SQS.
    sqs = boto3.resource('sqs', region_name=SQS_REGION)
    queue = sqs.get_queue_by_name(QueueName=SQS_QUEUE)
    response = queue.send_message(
        MessageBody=json.dumps(message)
    )

    return f"OK (ID: {response.get('MessageId')})"


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
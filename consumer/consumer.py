#!/usr/bin/env python
import datetime
import json
import os
import time

import boto3
import requests

JENKINS_URL = os.environ['JENKINS_URL']
SQS_QUEUE = os.environ['SQS_QUEUE']
SQS_REGION = os.environ['SQS_REGION']

sqs = boto3.resource('sqs', region_name=SQS_REGION)
queue = sqs.get_queue_by_name(QueueName=SQS_QUEUE)

print("Webhook consumer starting up!")

while True:
    for message in queue.receive_messages(
            WaitTimeSeconds=20, MaxNumberOfMessages=10):
        print(f"Got message: {message.message_id} at {datetime.datetime.now().isoformat()}")
        parsed = json.loads(message.body)
        original_headers = parsed['headers']
        payload = parsed['payload']

        # Set up our headers.
        headers = {}
        headers['Content-Type'] = "application/json"
        headers['X-Github-Event'] = original_headers['X-Github-Event']

        # Post the message to jenkins.
        resp = requests.post(
            JENKINS_URL,
            headers=headers,
            data=json.dumps(payload),
            verify=False
        )
        print(resp.text)

        # Delete the message if we made it this far.
        message.delete()

    time.sleep(5)

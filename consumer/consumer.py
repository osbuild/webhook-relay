#!/usr/bin/env python
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

while True:
    try:
        for message in queue.receive_messages():
            print(f"Got message: {message.message_id}")
            parsed = json.loads(message.body)
            original_headers = parsed['headers']
            payload = parsed['payload']

            # Set up our headers.
            headers = {}
            headers['Content-Type'] = "application/json"
            headers['X-GitHub-Event'] = "push"

            # Post the message to jenkins.
            resp = requests.post(
                JENKINS_URL,
                headers=headers,
                data=json.dumps(payload),
                verify=False
            )
            print(resp.text)

    except Exception:
        pass

    time.sleep(10)
# Webhook receiver and consumer

Getting GitHub webhooks on a private network is a challenge. The easiest
method is to open a port and allow GitHub's IP addresses to reach the port.
However, that does not work well if you do not have access to adjust the
network configuration.

## How does it work?

The receiver and consumer in this repository work this way:

```
    +------------+
    | GitHub     |                      +------------------+
    +------------+           +--------->+ AWS SQS          |
         |                   |          +------------------+
         |                   |                    ^
         |           +---------------+            |
         +---------->+ receiver      |            |
                     +---------------+            |
                                                  |
                                                  |
WAN                                               |
+----------------------------------------------------------+
LAN                                               |
                                                  |
       +-----------------------+     +---------------------+
       | jenkins               |     | consumer            |
       | (or any other system) |     +---------------------+
       |                       |                  |
       +------------------------<-----------------+
```

Here is a run-down of what happens:

1. GitHub sends a webhook to the receiver
2. The receiver packages the headers and payload (JSON) from GitHub into a
   message that is sent to Amazon's Simple Queue Service.
3. A consumer inside the firewall connects to SQS frequently to look for new
   mesages.
4. When a message appears in SQS, the consumer sends the JSON payload (with a
   subset of the original GitHub headers) to an internal server, such as
   Jenkins.
5. If the consumer delivers the message successfully, it deletes the message
   from SQS.

## How much does it cost?

The [SQS pricing] is very friendly for this setup since you get the first one
million messages for free and each additional million requests are $0.40 USD
each.

💸 **Keep in mind that data transfer costs are still applied!** The first 1 GB
of data transferred per month is free and the next 10TB is $0.09 per GB. These
messages are so small that the transfer costs should remain low.

💣 Also, remember that these prices are for the lowest prices regions, like
*us-east-1* and *us-east-2*. Different regions have different cost structures,
so be sure to check that before deploying.

## How do I run it?

The receiver works well with docker-compose:

```yaml
---
  version: "3"
  services:
    webhook-receiver:
      build: /opt/webhook-relay/receiver
      container_name: webhook-receiver
      ports:
        - 5000:5000
      environment:
        - GITHUB_SECRET=         # The secret that GitHub sends with webhooks
        - SQS_QUEUE=             # SQS queue name at AWS
        - SQS_REGION=            # AWS region (check pricing first!)
        - AWS_ACCESS_KEY_ID=     # AWS access key ID for valid AWS user
        - AWS_SECRET_ACCESS_KEY= # AWS access secret key for valid AWS user
```

You can run the consumer in a very similar way:

```yaml
---
  version: "3"
  services:
    webhook-receiver:
      build: /opt/webhook-relay/consumer
      container_name: webhook-consumer
      ports:
        - 5000:5000
      environment:
        - JENKINS_URL=           # URL to jenkins (usually https://jenkins/github-webhook/)
        - SQS_QUEUE=             # SQS queue name at AWS
        - SQS_REGION=            # AWS region (check pricing first!)
        - AWS_ACCESS_KEY_ID=     # AWS access key ID for valid AWS user
        - AWS_SECRET_ACCESS_KEY= # AWS access secret key for valid AWS user
```

## Security

Always set a `GITHUB_SECRET` so the receiver can verify that GitHub is the
true source of the webhook.

Also, consider using two highly restricted AWS users for publishing and
consuming SQS messages. You can use IAM policies to restrict the access such
that each part of the deployment can only do the things it is allowed to do.

Example webhook receiver policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "sqs:GetQueueUrl",
                "sqs:SendMessage"
            ],
            "Resource": "arn:aws:sqs:SQS_REGION:ACCOUNT_NUMBER:SQS_QUEUE_NAME"
        }
    ]
}
```

Example webhook consumer policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl",
                "sqs:ReceiveMessage"
            ],
            "Resource": "arn:aws:sqs:SQS_REGION:ACCOUNT_NUMBER:SQS_QUEUE_NAME"
        }
    ]
}
```

Be sure to set the `SQS_REGION`, `ACCOUNT_NUMBER`, and `SQS_QUEUE_NAME` to the
proper values in these policies.

[SQS pricing]: https://aws.amazon.com/sqs/pricing/
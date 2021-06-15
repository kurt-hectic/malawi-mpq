# WMO cloud based MQP infrastructure setup
This repository contains the code to setup an Amazon Web Services based infrastructure for the disseminaton of observations. It is used in WMO WIS 2.0 demonstrator projects.

## architecture
The infrastructure consists of an S3 bucket, to which new observations are uploaded, users and roles allowing upload, a (dockerized) lambda function, which processes the incoming files and creates and sends a notification to an (external) MQP broker.
The notification message structure is based on the [draft specifications](https://github.com/wmo-im/GTStoWIS2) of the WMO Task Team on Protocols. 
If the filesize of an observation is below a threshold it will be embedded in the notification, in addition to a link from where it can be downloaded, being included in the notification.

## configuration
The lambda function can be configured using environment variables, that can be set using the AWS CLI. The variables that are supported are:
- S3_PUBLIC_URL: The URL of the public folder from which the observations can be downloaded
- MAX_SIZE: The threshold for embedding of observations into the notification
- MALAWI_TOPIC: The routing key (topic) used for the observations
- CLOUDAMQP_URL: The connection string for connecting to the external broker

## code
The script [AWS_setup.ps1](https://github.com/kurt-hectic/malawi-mpq/tree/main/publisher_lambda) (Windows Power Shell), creates S3 buckets, roles, a docker image for the lambda function, based on the [app.py](https://github.com/kurt-hectic/malawi-mpq/blob/main/publisher_lambda/app.py) code, an execution policy, other permissions as well as a trigger linking the S3 bucket, incoming folder, with the lambda function.

There is also a [consumer script](https://github.com/kurt-hectic/malawi-mpq/blob/main/consumer/consume.py), which can be used to obtain the observations which are published.

## external components
Not included in the setup, and created manually, are:
1. A Windows Server and SQL Server, which collect the observations from Automatic Weather Stations.
2. A MQP brokwer, which was setup using the cloudamqp service.

# local testing
The docker image can be tested locally like this (env_aws file not included in github):
```docker build -t s3tomqp:latest . && docker run --rm -it -p 9000:8080 --env-file env_aws s3tomqp```

A test event can be sent by invoking the image with curl:
```curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test/s3-event.json```

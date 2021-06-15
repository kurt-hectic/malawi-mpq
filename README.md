# WMO cloud based MQP infrastructure setup
This repository contains the code to setup an Amazon Web Services based infrastructure for the disseminaton of observations. It is used in WMO WIS 2.0 demonstrator projects.

## architecture
The infrastructure consists of an S3 bucket, to which new observations are uploaded, a lambda function, which processes the incoming files and creates and sends a notification to an (external) MQP broker.
The notification message structure is based on the [draft specifications](https://github.com/wmo-im/GTStoWIS2) of the WMO Task Team on Protocols.

## code
The script AWS_setup.ps1 (Windows Power Shell), creates S3 buckets, roles, a docker image for the lambda function, based on the app.py code in the directory publisher_lambda, an execution policy, other permissions as well as a trigger linking the S3 bucket, incoming folder, with the lambda function.

There is also a consumer script, which can be used to obtain the observations which are published.

## external components
Not incliuded in the setup, and created manually, are:
1. A Windows Server and SQL Server, which collect the observations from Automatic Weather Stations.
2. A MQP brokwer, which was setup using the cloudamqp service.

# local testing
The docker image can be tested locally like this:
```docker build -t s3tomqp:latest . && docker run --rm -it -p 9000:8080 --env-file env_aws s3tomqp```

A test event can be sent by invoking the image with curl:
```curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test/s3-event.json```
import base64
import sys
import pika
import json
import boto3
import hashlib
import os
import json
import re
import logging

import urllib.parse

from datetime import datetime,timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info('Loading function')
s3 = boto3.client('s3')

# environment variables to configure the code
S3_PUBLIC_URL = os.environ.get('S3_PUBLIC_URL')
MAX_SIZE = int(os.environ.get('MAX_SIZE'))
MALAWI_TOPIC = os.environ.get('MALAWI_TOPIC')
MQP_URL = os.environ.get('CLOUDAMQP_URL')

def make_mqp_message(s3_object,rel_path):
    """creates a MQP notification based on the WIS 2.0 message structure.
    Embedds the file, if below message max size
    """

    size = s3_object["ContentLength"]
    body = s3_object["Body"].read()
    
    if not size == len(body):
        raise Exception("size {} does not correspond to content length {}".format(len(body),size))
    
    pub_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")
    
    hex_digest = hashlib.sha512(body).hexdigest()
       
    # message structure
    message = {
        "pubTime" : pub_time,
        "baseUrl" : S3_PUBLIC_URL,
        "integrity" : { "method" : "sha512" , "value" : hex_digest },
        "relPath" : "/{}".format(rel_path),
        "size" : size
    }

    # embed the file if below max size
    if size <= MAX_SIZE:
        logger.info("embedding file into message")
        base64_string = base64.b64encode(body).decode("ascii")
        message["content"] = {"encoding" : "base64", "value" : base64_string }

    return message


def publish_message(message):
    """connects to the broker and sends the notiifcation. Closes connection, no persistence."""

    logger.debug("establishing connection to broker")
    params = pika.URLParameters(MQP_URL)
    connection = pika.BlockingConnection(params)

    channel = connection.channel()
    logger.debug("publishing message to broker")
    channel.basic_publish(exchange='amq.topic', # topic based exchange
                      routing_key=MALAWI_TOPIC, # static routing key 
                      body=message)

    connection.close()


def handler(event, context):
    """function called by AWS and linked to the S3 trigger
    Extracts bucket, file path and name.
    Moves file into public directory with subdirectories based on topic.
    Calls methods to create and send message structure."""
    
    logger.debug("Received event: " + json.dumps(event, indent=2))

    # filename and path
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    path, filename = os.path.split(key)
    
    logger.info("incoming file {} {}".format(path,filename))
   
    try:
        # move file into final position 
        rel_path = "{}/{}".format(MALAWI_TOPIC.replace('.','/'),filename)
        new_key = "public/{}".format(rel_path)
        logger.debug("moving {bucket}/{} to {bucket}/{}".format(key,new_key,bucket=bucket))
        response = s3.copy_object(Bucket=bucket, Key=new_key, CopySource={"Bucket" : bucket , "Key" : key }   )
        response = s3.delete_object(Bucket=bucket, Key=key)

        # get file content
        logger.debug("getting {}/{}".format(bucket,new_key))
        response = s3.get_object(Bucket=bucket, Key=new_key)

        # create message and send to broker
        logger.debug("sending message with topic {} to broker {}".format( MALAWI_TOPIC ,re.sub( r":[^/]+@", ":*****@" , MQP_URL ) ))
        mqp_notification = make_mqp_message(response,rel_path)
        mqp_notification = json.dumps(mqp_notification,indent=4)
        publish_message(mqp_notification)
        
        logger.info("message processed and published")

        return 0
    except Exception as e:
        logger.error("procesing error {}".format(e))
        raise e
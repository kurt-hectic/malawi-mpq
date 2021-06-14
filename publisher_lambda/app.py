import base64
import sys
import pika
import json
import boto3
import hashlib
import os
import json
import re

import urllib.parse

from datetime import datetime,timezone

print('Loading function')
s3 = boto3.client('s3')

S3_PUBLIC_URL = os.environ.get('S3_PUBLIC_URL')
MAX_SIZE = int(os.environ.get('MAX_SIZE'))
MALAWI_TOPIC = os.environ.get('MALAWI_TOPIC')
MQP_URL = os.environ.get('CLOUDAMQP_URL')

def make_mqp_message(s3_object,rel_path):

    size = s3_object["ContentLength"]
    body = s3_object["Body"].read()
    
    if not size == len(body):
        raise Exception("size {} does not correspond to content length {}".format(len(body),size))
    
    pub_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%f")
    
    hex_digest = hashlib.sha512(body).hexdigest()
       
    message = {
        "pubTime" : pub_time,
        "baseUrl" : S3_PUBLIC_URL,
        "integrity" : { "method" : "sha512" , "value" : hex_digest },
        "relPath" : "/{}".format(rel_path),
        "size" : size
    }

    if size <= MAX_SIZE:
        base64_string = base64.b64encode(body).decode("ascii")
        message["content"] = {"encoding" : "base64", "value" : base64_string }

    return message


def publish_message(message):

    url = MQP_URL

    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)

    channel = connection.channel() # start a channel
    channel.basic_publish(exchange='amq.topic',
                      routing_key=MALAWI_TOPIC,
                      body=message)

    connection.close()


def handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    path, filename = os.path.split(key)
   
    
    try:
        # move file into final position 
        rel_path = "{}/{}".format(MALAWI_TOPIC.replace('.','/'),filename)
        new_key = "public/{}".format(rel_path)
        print("moving {bucket}/{} to {bucket}/{}".format(key,new_key,bucket=bucket))
        response = s3.copy_object(Bucket=bucket, Key=new_key, CopySource={"Bucket" : bucket , "Key" : key }   )
        response = s3.delete_object(Bucket=bucket, Key=key)

        # get file content
        print("getting {}/{}".format(bucket,new_key))
        response = s3.get_object(Bucket=bucket, Key=new_key)

        # create message and send to broker
        print("sending message with topic {} to broker {}".format( MALAWI_TOPIC ,re.sub( r":[^/]+@", ":*****@" , MQP_URL ) ))
        mqp_notification = make_mqp_message(response,rel_path)
        mqp_notification = json.dumps(mqp_notification,indent=4)
        publish_message(mqp_notification)
        
        print("message processed and published")

        return 0
    except Exception as e:
        print("procesing error {}".format(e))
        raise e
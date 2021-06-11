import pika
import os
import requests
import json
import base64
import hashlib

from jsonschema import validate

url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/%2f')
routing_key = "mw.#"
out_dir = r"./out"

schema = json.load(open("message-schema.json"))

params = pika.URLParameters(url)
connection = pika.BlockingConnection(params)
channel = connection.channel() # start a channel

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange="amq.topic", queue=queue_name, routing_key=routing_key)

def parse_mqp_message(message,topic):
    
    message = json.loads(message)
    validate(instance=message, schema=schema)
        
    content = base64.b64decode(message["content"]["value"]) if "content" in message else requests.get(message["baseUrl"] + message["relPath"]).content
        
    if not len(content) == message["size"] or not hashlib.sha512(content).hexdigest() == message["integrity"]["value"] :
        raise Exception("integrity issue")

    path, filename = os.path.split(message["relPath"])
    topic_dir = os.path.join( out_dir , topic.replace(".","/") )
    
    os.makedirs( topic_dir , exist_ok=True )
    out_file = os.path.join(topic_dir,filename)
    with open( out_file , "wb" ) as fp:
        fp.write(content)
        
    print("obtained and wrote {}".format(out_file))

def callback(ch, method, properties, body):
    topic = method.routing_key
    
    print(" [x] Received message with topic " + topic )
    
    parse_mqp_message(body,topic)
    

channel.basic_consume(queue_name,
                      callback,
                      auto_ack=True)

print(' [*] Waiting for messages:')
channel.start_consuming()
connection.close()
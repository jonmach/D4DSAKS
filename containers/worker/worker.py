#!/usr/bin/env python

from mxnet import gluon, nd, image
import mxnet as mx
from mxnet.gluon.data.vision import transforms
from gluoncv import utils
from gluoncv.model_zoo import get_model
import psycopg2
import pika
import time, os, json
from azure.storage.blob import ContainerClient

import cv2
import numpy as np

# Get Environment Vars
RMQ_USER=os.environ["RMQ_USER"]      # RabbitMQ Username
RMQ_PASS=os.environ["RMQ_PASS"]      # RabbitMQ Password
RMQ_HOST=os.environ["RMQ_HOST"]      # RabbitMQ Hostname
SQL_HOST=os.environ["SQL_HOST"]      # SQL Hostname
SQL_DB=os.environ["SQL_DB"]          # SQL Database
SQL_USER=os.environ["SQL_USER"]      # SQL Username
SQL_PASS=os.environ["SQL_PASS"]      # SQL Password
STG_ACNAME=os.environ["STG_ACNAME"]  # Storage Account Name
STG_ACKEY=os.environ["STG_ACKEY"]    # Storage Account Key
LOGTODB=os.environ["LOGTODB"]        # Log data to Database?

# Location of Images on blob storage
CONNECTION_STRING="DefaultEndpointsProtocol=https" + \
    ";EndpointSuffix=core.windows.net" + \
    ";AccountName="+STG_ACNAME+";AccountKey="+STG_ACKEY

container = ContainerClient.from_connection_string(CONNECTION_STRING, container_name="cifar")

class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
net = get_model('cifar_resnet110_v1', classes=10, pretrained=True)

transform_fn = transforms.Compose([
        transforms.Resize(32), transforms.CenterCrop(32), transforms.ToTensor(),
        transforms.Normalize([0.4914, 0.4822, 0.4465], [0.2023, 0.1994, 0.2010])
    ])

def predictCategory(fname):
    blob_client = container.get_blob_client(fname)
    imgStream = blob_client.download_blob().readall()
    img = mx.ndarray.array(cv2.imdecode(np.frombuffer(imgStream, np.uint8), -1))
    img = transform_fn(img)
    
    pred = net(img.expand_dims(axis=0))
    ind = nd.argmax(pred, axis=1).astype('int')
    print('%s is classified as [%s], with probability %.3f.'% 
          (fname, class_names[ind.asscalar()], nd.softmax(pred)[0][ind].asscalar()))
    return ind.asscalar(), nd.softmax(pred)[0][ind].asscalar()
    
def InsertResult(connection, fname, category, prediction, prob):
    count=0
    try:
        cursor = connection.cursor()
        qry = """ INSERT INTO CATEGORY_RESULTS (FNAME, CATEGORY, PREDICTION, CONFIDENCE) VALUES (%s,%s,%s,%s)"""
        record = (fname, category, prediction, prob)
        cursor.execute(qry, record)

        connection.commit()
        count = cursor.rowcount
        
    except (Exception, psycopg2.Error) as error :
        if(connection):
            print("Failed to insert record into category_results table", error)

    finally:
        cursor.close()
        return count

#
# Routine to pull message from queue, call classifier, and insert result to the DB
#
def callback(ch, method, properties, body):
    data = json.loads(body)
    fname = data['image']
    cat = data['category']
    pred, prob = predictCategory(fname)
    if (LOGTODB == 1):
        count = InsertResult(pgconn, fname, int(cat), int(pred), float(prob))
    else:
        count = 1  # Ensure the message is ack'd and removed from queue
        
    if (count > 0):
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        ch.basic_nack(delivery_tag=method.delivery_tag)

pgconn = psycopg2.connect(user=SQL_USER, password=SQL_PASS, 
                          host=SQL_HOST, port="5432", database=SQL_DB)
credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
parameters = pika.ConnectionParameters(RMQ_HOST, 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.queue_declare(queue='image_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='image_queue', on_message_callback=callback)

channel.start_consuming()

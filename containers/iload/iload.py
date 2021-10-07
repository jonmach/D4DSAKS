#!/usr/bin/env python
import sys, os, json, pika
import psycopg2
from azure.storage.blob import ContainerClient

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

# Set up database table if needed
cmd = """ 
            CREATE TABLE IF NOT EXISTS CATEGORY_RESULTS (
            FNAME         VARCHAR(1024) NOT NULL,
            CATEGORY      NUMERIC(2) NOT NULL,
            PREDICTION    NUMERIC(2) NOT NULL,
            CONFIDENCE    REAL);
        """
pgconn = psycopg2.connect(user=SQL_USER, password=SQL_PASS, 
                host=SQL_HOST, port="5432", database=SQL_DB)
cur = pgconn.cursor()
cur.execute(cmd)
cur.close()
pgconn.commit()

# Load all images in defined storage account
CONNECTION_STRING="DefaultEndpointsProtocol=https" + \
    ";EndpointSuffix=core.windows.net" + \
    ";AccountName="+STG_ACNAME+";AccountKey="+STG_ACKEY
ROOT="/CIFAR-10-images"             # This is where the images are held
container = ContainerClient.from_connection_string(CONNECTION_STRING, container_name="cifar")

rLen = len(ROOT)
classes = ('airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')        

# Determine the expected category by parsing the directory (after the root path)
def fnameToCategory(fname):
    for c in classes:
        if (fname.find(c) > rLen):
            return (classes.index(c))
    return -1 # This should never happen

IMGS=[]
blob_list = container.list_blobs()
for blob in blob_list:
    if blob.name.endswith(('.png', '.jpg', '.jpeg')):
        cat = fnameToCategory(blob.name)
        data = {"image" : blob.name, "category": cat, "catName": classes[cat]}
        message = json.dumps(data)  
        IMGS.append(message)
print("Number of Images to add to queue = ", len(IMGS))

# Now write them into the queue
credentials = pika.PlainCredentials(RMQ_USER, RMQ_PASS)
parameters = pika.ConnectionParameters(RMQ_HOST, 5672, '/', credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue='image_queue', durable=True)

for i in IMGS:
    channel.basic_publish( exchange='', routing_key='image_queue', body=i,
        properties=pika.BasicProperties(delivery_mode=2,)
    )
    print("Queued ", i)

connection.close()


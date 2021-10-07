FROM ubuntu

RUN apt-get update 
RUN apt-get install -y python3 python3-pip 

RUN pip3 install --upgrade mxnet gluoncv pika 
RUN pip3 install psycopg2-binary 

RUN pip install azureml-sdk
RUN pip install azureml-sdk[notebooks]
RUN pip install azure.ai.formrecognizer
RUN pip install azure.storage.blob
RUN pip install opencv-python

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install ffmpeg libsm6 libxext6  -y


# Add worker logic necessary to process queue items
ADD  worker.py /

# Start the worker
CMD ["python3", "./worker.py" ]


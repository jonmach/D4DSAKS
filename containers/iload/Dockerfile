FROM ubuntu

RUN apt-get update
RUN apt-get install -y python3 python3-pip

RUN apt-get update && apt-get install -y poppler-utils net-tools vim
RUN pip install azureml-sdk
RUN pip install azureml-sdk[notebooks]
RUN pip install azure.ai.formrecognizer
RUN pip install azure.storage.blob
RUN pip install jsonify
RUN pip install pika
RUN pip install psycopg2-binary 

ADD  iload.py /

CMD ["python3", "./load.py" ]


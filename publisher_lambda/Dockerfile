FROM public.ecr.aws/lambda/python:3.8

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV S3_PUBLIC_URL="https://malawi-mqp.s3.eu-central-1.amazonaws.com/public"
ENV MAX_SIZE=4000
ENV MALAWI_TOPIC="mw.blantyre_chileka.observation.surface.land.automatic.tropics.0-90w"
# replace this with actual connection credentials during run
ENV MQP_URL="amqp://guest:guest@localhost:5672/%2f"  

COPY app.py   ./
CMD ["app.handler"]   
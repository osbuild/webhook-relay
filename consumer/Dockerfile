FROM python:latest
RUN pip install boto3 requests && rm -rf ~/.cache
COPY consumer.py /
CMD ["python", "-u", "/consumer.py"]
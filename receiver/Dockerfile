FROM python:latest
RUN pip install boto3 flask && rm -rf ~/.cache
COPY receiver.py /
EXPOSE 5000
CMD ["/receiver.py"]
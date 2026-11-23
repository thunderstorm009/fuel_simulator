FROM python:3.12-alpine

WORKDIR /app

COPY receiver.py .

RUN mkdir -p /logs

EXPOSE 5001

CMD ["python", "-u", "receiver.py"]

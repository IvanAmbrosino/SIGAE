# Dockerfile for tle-pass-activity-generator... escucha en el topic de Kafka y genera actividades TLE
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "infrastructure/kafka_consumer.py"]

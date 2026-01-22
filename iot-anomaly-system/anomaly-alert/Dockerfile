# Use a small Python base
FROM python:3.12-slim

# Avoid interactive prompts and disable pip cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only what's needed
RUN pip install --no-cache-dir kafka-python

# Copy the alert service
COPY alert_service.py /app/alert_service.py

# Default env can be overridden by docker-compose
ENV KAFKA_BOOTSTRAP="kafka:9092" \
    KAFKA_TOPIC_ANOMALY="iot.sensor.anomaly" \
    KAFKA_GROUP_ID="anomaly-alert-group" \
    SCORE_THRESHOLD="3.0" \
    ONLY_FLAGGED="true"

CMD ["python", "/app/alert_service.py"]
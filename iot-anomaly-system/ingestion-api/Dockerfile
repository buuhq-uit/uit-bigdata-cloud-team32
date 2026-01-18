FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy and install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir kafka-python fastapi uvicorn pydantic

# Copy app code
COPY . .

EXPOSE 8000
# Reasonable default; override via compose env
ENV KAFKA_BOOTSTRAP=kafka:9092

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
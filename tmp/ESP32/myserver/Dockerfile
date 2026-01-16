FROM python:3.9
WORKDIR /app
COPY app.py .
RUN pip install flask kafka-python
CMD ["python", "app.py"]
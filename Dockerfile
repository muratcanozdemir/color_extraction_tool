# Use the official Python image as the base image
FROM python:3.10-slim-buster

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY configs/ ./configs/
COPY tasks/ ./tasks
COPY templates/ ./templates

EXPOSE 8000

CMD ["gunicorn", "-c", "configs/gunicorn_config.py"]

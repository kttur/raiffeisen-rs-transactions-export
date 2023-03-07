FROM python:3.10-slim as base
WORKDIR /app/
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY config ./config/
COPY src ./src/
COPY main.py .

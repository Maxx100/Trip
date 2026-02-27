FROM python:3.11-slim

WORKDIR /app

COPY services/website/requirements.txt ./requirements.txt
COPY core/logger/requirements.txt ./core/logger/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r core/logger/requirements.txt

COPY core ./core
COPY services/website .

RUN mkdir -p /app/logs

EXPOSE 443 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-keyfile", "/app/certificate.key", "--ssl-certfile", "/app/fullchain.pem"]
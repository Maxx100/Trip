FROM python:3.11-slim

WORKDIR /app

COPY services/accounts .
COPY core ./core

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r core/logger/requirements.txt

RUN mkdir -p /app/logs

EXPOSE 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

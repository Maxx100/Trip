FROM python:3.11-slim

WORKDIR /app

COPY core ./core
COPY services/website .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r core/logger/requirements.txt

RUN mkdir -p /app/logs

# open port
EXPOSE 80

CMD ["python", "main.py"]
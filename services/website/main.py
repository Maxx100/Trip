from fastapi import FastAPI, Response
import logging
import threading
import requests
import time
from core.logger.logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)

@app.get("/")
def read_root():
    return Response(content="s4vaki", media_type="text/plain; charset=utf-8")

def simulate_user_creation():
    time.sleep(10) 
    
    try:
        response = requests.post(
            'http://accounts:5000/create_user',
            json={
                'email': 'test_from_web@example.com',
                'password': 'secure_password_123'
            }
        )
        logger.info(f"User creation response: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Failed to call accounts service: {e}")

if __name__ == '__main__':
    test_thread = threading.Thread(target=simulate_user_creation, daemon=True)
    test_thread.start()

    logger.info("Starting website service with Uvicorn...")
    
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=443, 
        ssl_keyfile="/app/certificate.key", 
        ssl_certfile="/app/fullchain.pem"
    )

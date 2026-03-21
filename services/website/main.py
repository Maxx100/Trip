from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import logging
from pydantic import BaseModel
from email_notifier import Notify
from core.logger.logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)


class LeadRequest(BaseModel):
    name: str
    phone: str
    email: str
    wishes: str = ""


notifier = Notify()


@app.post("/api/lead")
def create_lead(lead: LeadRequest):
    subject = "Новая заявка с сайта trip-kzn.ru"
    message = (
        "Новая заявка с формы сайта:\n\n"
        f"Имя: {lead.name}\n"
        f"Телефон: {lead.phone}\n"
        f"Email: {lead.email}\n"
        f"Пожелания: {lead.wishes}\n"
    )

    try:
        notifier.send_email(subject=subject, message=message)
        logger.info("Lead email sent successfully")
        return {"status": "ok"}
    except Exception as error:
        logger.exception("Failed to send lead email")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {error}")


app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == '__main__':
    logger.info("Starting website service with Uvicorn...")
    
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=443, 
        ssl_keyfile="/app/certificate.key", 
        ssl_certfile="/app/fullchain.pem"
    )

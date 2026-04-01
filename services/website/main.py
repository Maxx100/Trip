from pathlib import Path
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import logging
from pydantic import BaseModel
from email_notifier import Notify
from currency_rate import CurrencyRate
from core.logger.logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class LeadRequest(BaseModel):
    name: str
    phone: str
    email: str
    wishes: str = ""


notifier = Notify()
currency_rate = CurrencyRate()
currency_cache_lock = threading.Lock()
currency_cache: dict = {"updated_at": 0.0, "data": None}
CURRENCY_CACHE_TTL_SECONDS = 1800


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


@app.get("/api/currency-rate")
def get_currency_rate():
    now = time.time()

    with currency_cache_lock:
        if currency_cache["data"] and (now - currency_cache["updated_at"] < CURRENCY_CACHE_TTL_SECONDS):
            return {
                "status": "ok",
                "source": "cache",
                "updated_at": int(currency_cache["updated_at"]),
                "rates": currency_cache["data"],
            }

    try:
        fresh_data = currency_rate.fetch()
    except Exception as error:
        logger.exception("Failed to fetch currency rates")
        raise HTTPException(status_code=502, detail=f"Failed to fetch currency rates: {error}")

    with currency_cache_lock:
        currency_cache["data"] = fresh_data
        currency_cache["updated_at"] = now

    return {
        "status": "ok",
        "source": "fresh",
        "updated_at": int(now),
        "rates": fresh_data,
    }


@app.get("/", include_in_schema=False)
def home_page():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/why-us", include_in_schema=False)
def why_us_page():
    return FileResponse(STATIC_DIR / "why-us.html")


@app.get("/privacy", include_in_schema=False)
def privacy_page():
    return FileResponse(STATIC_DIR / "privacy.html")


@app.get("/currency-rate", include_in_schema=False)
def currency_rate_page():
    return FileResponse(STATIC_DIR / "currency-rate.html")


@app.get("/how-selection-works", include_in_schema=False)
def how_selection_works_page():
    return FileResponse(STATIC_DIR / "how-selection-works.html")


@app.get("/link", include_in_schema=False)
def placeholder_link_page():
    return RedirectResponse(url="/#groups", status_code=307)


@app.get("/styles.css", include_in_schema=False)
def styles_css():
    return FileResponse(STATIC_DIR / "styles.css")


@app.get("/script.js", include_in_schema=False)
def script_js():
    return FileResponse(STATIC_DIR / "script.js")


app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def deny_unknown_paths(path: str):
    if path.endswith(".html"):
        raise HTTPException(status_code=404, detail="Not found")
    raise HTTPException(status_code=404, detail="Not found")

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

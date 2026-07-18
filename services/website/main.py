from pathlib import Path
import json
import threading
import time

from fastapi import FastAPI, HTTPException, Request
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

HTTP_REDIRECT_PORT = 80
http_redirect_app = FastAPI(docs_url=None, redoc_url=None)


@http_redirect_app.api_route("/{path:path}", methods=["GET", "HEAD"])
def redirect_to_https(request: Request, path: str):
    target = f"https://{request.url.hostname}{request.url.path}"
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(target, status_code=301)


def _run_http_redirect_server() -> None:
    import uvicorn

    config = uvicorn.Config(http_redirect_app, host="0.0.0.0", port=HTTP_REDIRECT_PORT, log_level="warning")
    try:
        uvicorn.Server(config).run()
    except Exception:
        logger.exception("HTTP->HTTPS redirect server on port %s failed", HTTP_REDIRECT_PORT)


@app.on_event("startup")
def start_http_redirect_server() -> None:
    thread = threading.Thread(target=_run_http_redirect_server, daemon=True, name="http-redirect")
    thread.start()


class LeadRequest(BaseModel):
    name: str
    phone: str
    email: str
    wishes: str = ""


notifier = Notify()
currency_rate = CurrencyRate()
currency_cache_lock = threading.Lock()
currency_cache: dict = {"updated_at": 0.0, "data": None, "last_error": None}
CURRENCY_REFRESH_INTERVAL_SECONDS = 1800
currency_worker_stop_event = threading.Event()
currency_worker_thread: threading.Thread | None = None
CURRENCY_CACHE_FILE = BASE_DIR / "logs" / "currency_cache.json"


def _save_currency_cache_to_file(data: dict, updated_at: float) -> None:
    CURRENCY_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": int(updated_at),
        "rates": data,
    }
    with CURRENCY_CACHE_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)


def _load_currency_cache_from_file() -> bool:
    if not CURRENCY_CACHE_FILE.exists():
        return False

    try:
        with CURRENCY_CACHE_FILE.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        rates = payload.get("rates")
        updated_at = float(payload.get("updated_at", 0))
        if not rates:
            return False

        with currency_cache_lock:
            currency_cache["data"] = rates
            currency_cache["updated_at"] = updated_at
            currency_cache["last_error"] = None
        return True
    except Exception as error:
        logger.warning("Failed to load currency cache from file: %s", error)
        return False


def refresh_currency_cache_once() -> None:
    now = time.time()
    try:
        fresh_data = currency_rate.fetch()
    except Exception as error:
        logger.exception("Failed to fetch currency rates in background refresh")
        with currency_cache_lock:
            currency_cache["last_error"] = str(error)
        return

    with currency_cache_lock:
        currency_cache["data"] = fresh_data
        currency_cache["updated_at"] = now
        currency_cache["last_error"] = None

    try:
        _save_currency_cache_to_file(fresh_data, now)
    except Exception as error:
        logger.warning("Failed to save currency cache to file: %s", error)


def currency_worker_loop() -> None:
    while not currency_worker_stop_event.is_set():
        refresh_currency_cache_once()
        currency_worker_stop_event.wait(CURRENCY_REFRESH_INTERVAL_SECONDS)


@app.on_event("startup")
def start_currency_worker() -> None:
    _load_currency_cache_from_file()

    global currency_worker_thread
    currency_worker_stop_event.clear()
    currency_worker_thread = threading.Thread(target=currency_worker_loop, daemon=True, name="currency-worker")
    currency_worker_thread.start()


@app.on_event("shutdown")
def stop_currency_worker() -> None:
    currency_worker_stop_event.set()


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
    with currency_cache_lock:
        cached_data = currency_cache["data"]
        updated_at = currency_cache["updated_at"]
        last_error = currency_cache["last_error"]

    if not cached_data:
        raise HTTPException(
            status_code=503,
            detail="Currency rates are being prepared. Please try again shortly.",
        )

    return {
        "status": "ok",
        "source": "cache",
        "updated_at": int(updated_at),
        "rates": cached_data,
        "warning": last_error,
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


@app.get("/reviews", include_in_schema=False)
def reviews_page():
    return FileResponse(STATIC_DIR / "reviews.html")


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

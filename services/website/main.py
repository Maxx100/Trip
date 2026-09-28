from pathlib import Path
import asyncio

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import logging
from pydantic import BaseModel
from email_notifier import Notify
from core.logger.logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

HTTP_PORT = 80
http_server_task: "asyncio.Task | None" = None


@app.middleware("http")
async def redirect_http_to_https(request: Request, call_next):
    if request.url.scheme == "http":
        target = f"https://{request.url.hostname}{request.url.path}"
        if request.url.query:
            target = f"{target}?{request.url.query}"
        return RedirectResponse(target, status_code=301)
    return await call_next(request)


@app.on_event("startup")
async def start_http_listener() -> None:
    import uvicorn

    global http_server_task
    config = uvicorn.Config(app, host="0.0.0.0", port=HTTP_PORT, log_level="warning", lifespan="off")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    http_server_task = asyncio.create_task(server.serve())


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

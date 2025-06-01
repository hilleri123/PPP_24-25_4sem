from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api.routes import router as api_router
from app.websocket.routes import router as ws_router

load_dotenv()

app = FastAPI(title="Lab-3 Async API")

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

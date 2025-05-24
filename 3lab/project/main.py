import warnings
from app.websocket import ws

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from fastapi import FastAPI
import uvicorn

from app.api.endpoints import corpus, user
from app.db.database import create_tables
app = FastAPI(title="Fuzzy Search API")
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(ws.router)
app.include_router(corpus.router, prefix="/corpus", tags=["corpus"])

@app.on_event("startup")
async def startup_event():
    create_tables()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
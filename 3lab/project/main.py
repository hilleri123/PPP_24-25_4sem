import warnings
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import uvicorn

from app.api.endpoints import corpus, user
from app.db.database import engine, SessionLocal, Base

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

async def startup():
    Base.metadata.create_all(bind=engine)
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield

app = FastAPI(title="Fuzzy Search API", lifespan=lifespan)

app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(corpus.router, prefix="/corpus", tags=["corpus"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

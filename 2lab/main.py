from fastapi import FastAPI
from app.api.endpoints import user, corpus

app = FastAPI()

app.include_router(user.router)
app.include_router(corpus.router)

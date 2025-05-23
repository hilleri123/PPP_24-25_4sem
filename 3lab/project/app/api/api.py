from app.schemas import schemas
from app.celery.tasks import search_algorithm_task, search_algorithm_result
from app.cruds import cruds
from app.db.db import get_db
from app.core import hashing
from app.core import auth
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/sign-up/", response_model=schemas.UserWithToken)
async def sign_up(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = cruds.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = cruds.create_user(db, user.email, user.password)

    token = auth.generate_access_token({
        "sub": created_user.email,
    })

    return schemas.UserWithToken(id=created_user.id, email=created_user.email, token=token)


@router.post("/login/", response_model=schemas.UserWithToken)
async def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = cruds.get_user_by_email(db, user.email)

    if db_user and hashing.verify_password(user.password, db_user.hashed_password):
        token = auth.generate_access_token({
            "sub": db_user.email,
        })

        return schemas.UserWithToken(id=db_user.id, email=db_user.email, token=token)

    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/users/me/", response_model=schemas.UserMe)
async def get_current_user(user: str = Depends(auth.get_current_user)):
    return user


@router.post("/upload_corpus/")
async def upload_corpus(corpus: schemas.CorpusCreate, db: Session = Depends(get_db)):
    return cruds.create_corpus(db, corpus.corpus_name, corpus.text)


@router.get("/corpuses/")
async def get_corpuses(db: Session = Depends(get_db)):
    return cruds.get_corpuses(db)


@router.post("/search_algorithm/")
async def search_algorithm(search_request: schemas.SearchRequest):
    task = search_algorithm_task.delay(search_request.word, search_request.algorithm, search_request.corpus_id)

    return {
        "task_id": task.id
    }


@router.get("/search_algorithm/{task_id}/status")
async def search_algorithm_status(task_id: str):
    result = search_algorithm_result(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None
    }

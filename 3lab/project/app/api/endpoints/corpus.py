from app.services.fuzzy_search import levenshtein_distance, ngram_distance
from app.models.corpus import Corpus
from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.corpus import SearchRequest
from celery.result import AsyncResult
from app.celery_worker import fuzzy_search_task
from app.db.session import get_db, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api")


@router.post("/search_algorithm")
def search_algorithm(
        word: str,
        algorithm: str,
        corpus_id: int,
        client_id: str,
        db: Session = Depends(get_db)
):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id).first()
    if not corpus:
        raise HTTPException(status_code=404, detail="Corpus not found")

    words = corpus.text.split()
    results = []

    for w in words:
        if algorithm == "levenshtein":
            distance = levenshtein_distance(word, w)
        elif algorithm == "ngram":
            distance = ngram_distance(word, w)
        else:
            raise HTTPException(status_code=400, detail="Invalid algorithm")

        results.append({"word": w, "distance": distance})

    return {
        "task_id": "generated_task_id",
        "client_id": client_id,
        "results": sorted(results, key=lambda x: x["distance"])[:5]
    }

@router.post("/async_search")
def start_search_task(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    task = fuzzy_search_task.delay(request.word, request.algorithm, request.corpus_id)
    return {"task_id": task.id}

@router.get("/task_status")
def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    try:
        result = AsyncResult(task_id)
        status = result.status  # тут может упасть, если backend не работает
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")

    return {
        "status": status,
        "progress": 100 if result.successful() else 0,
        "result": result.result if result.ready() else None
    }

@router.post("/async_search")
def start_search_task(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    task = fuzzy_search_task.delay(request.word, request.algorithm, request.corpus_id)
    return {"task_id": task.id}

@router.get("/task_status")
def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    try:
        result = AsyncResult(task_id)
        status = result.status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch task status: {str(e)}")

    return {
        "status": status,
        "progress": 100 if result.successful() else 0,
        "result": result.result if result.ready() else None
    }
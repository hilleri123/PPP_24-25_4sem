from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from app.services.fuzzy_search import levenshtein_distance, ngram_distance
from app.models.corpus import Corpus
from app.schemas.corpus import SearchRequest, SearchResponse
from app.celery_worker import celery_app
from app.db.session import get_db
from app.models.user import User
from app.db.session import get_current_user
from typing import List, Dict, Any
import time

router = APIRouter(prefix="/api")


@router.post("/search_algorithm", response_model=SearchResponse)
def search_algorithm(
        word: str,
        algorithm: str,
        corpus_id: int,
        db: Session = Depends(get_db)
):
    corpus = db.query(Corpus).filter(Corpus.id == corpus_id).first()
    if not corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )

    if algorithm not in ["levenshtein", "ngram"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid algorithm. Use 'levenshtein' or 'ngram'"
        )

    words = corpus.text.split()
    results = []

    start_time = time.time()
    for w in words:
        distance = levenshtein_distance(word, w) if algorithm == "levenshtein" else ngram_distance(word, w)
        results.append({"word": w, "distance": distance})
    execution_time = time.time() - start_time

    return {
        "results": sorted(results, key=lambda x: x["distance"])[:5],
        "execution_time": execution_time
    }


@router.post("/async_search", status_code=status.HTTP_202_ACCEPTED)
def start_search_task(
        request: SearchRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):

    if not db.query(Corpus).filter(Corpus.id == request.corpus_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corpus not found"
        )

    task = celery_app.send_task(
        "fuzzy_search_task",
        args=[request.word, request.algorithm, request.corpus_id],
        kwargs={"user_id": current_user.id}
    )
    return {"task_id": task.id}


@router.get("/task_status/{task_id}")
def get_task_status(
        task_id: str,
        current_user: User = Depends(get_current_user)
):
    try:
        result = AsyncResult(task_id)

        if result.failed():
            return {
                "status": "FAILURE",
                "error": str(result.result)
            }

        return {
            "status": result.status,
            "progress": result.info.get("progress", 0) if hasattr(result, "info") else 0,
            "result": result.result if result.ready() else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task status: {str(e)}"
        )

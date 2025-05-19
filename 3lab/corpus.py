from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.corpus import Corpus
from app.services.fuzzy_search import levenshtein_distance, ngram_distance

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
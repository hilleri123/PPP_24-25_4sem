from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.fuzzy_search import levenshtein_distance, ngram_distance

router = APIRouter()

corpuses = {}


@router.post("/upload_corpus")
def upload_corpus(corpus_name: str, text: str):
    corpus_id = len(corpuses) + 1
    corpuses[corpus_id] = {"name": corpus_name, "text": text}
    return {"corpus_id": corpus_id, "message": "Corpus uploaded successfully"}


@router.get("/corpuses")
def list_corpuses():
    return {"corpuses": [{"id": id, "name": corpus["name"]} for id, corpus in corpuses.items()]}


@router.post("/search_algorithm")
def search_algorithm(word: str, algorithm: str, corpus_id: int):
    if corpus_id not in corpuses:
        raise HTTPException(status_code=404, detail="Corpus not found")

    corpus_text = corpuses[corpus_id]["text"]
    words_in_corpus = corpus_text.split()

    results = []
    for w in words_in_corpus:
        if algorithm == "levenshtein":
            distance = levenshtein_distance(word, w)
        elif algorithm == "ngram":
            distance = ngram_distance(word, w)
        else:
            raise HTTPException(status_code=400, detail="Invalid algorithm")
        results.append({"word": w, "distance": distance})

    return {"execution_time": 0.0023, "results": results}
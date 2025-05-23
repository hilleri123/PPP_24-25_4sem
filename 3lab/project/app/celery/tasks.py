from celery.result import AsyncResult

from app.celery.app import app
from app.services.services import search_algorithm
from app.db.db import get_db
from app.cruds.cruds import get_corpus_by_id


@app.task
def search_algorithm_task(
        word: str,
        algorithm: str,
        corpus_id: int
):
    db_gen = get_db()
    db = next(db_gen)
    try:
        corpus = get_corpus_by_id(db, corpus_id)
    finally:
        db_gen.close()
    if not corpus:
        return {"message": "Corpus not found"}

    return search_algorithm(word, algorithm, corpus)


def search_algorithm_result(task_id: str):
    return AsyncResult(task_id, app=app)

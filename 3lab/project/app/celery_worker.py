import time
from celery import Celery
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.cruds import corpus as corpus_crud
from app.services import fuzzy_search
import logging

celery_app = Celery('tasks')
celery_app.config_from_object('app.celery_config')


@celery_app.task(name="fuzzy_search_task", bind=True)
def fuzzy_search_task(self, word: str, algorithm: str, corpus_id: int):
    print(f"Starting search with params: word='{word}', algorithm={algorithm}, corpus_id={corpus_id}")
    db: Session = SessionLocal()
    try:
        corpus = corpus_crud.get_corpus_by_id(db, corpus_id)
        if not corpus:
            return {"error": "Corpus not found"}

        words = list(set(corpus.text.split()))
        total = len(words)
        results = []

        for idx, w in enumerate(words):
            # Обновлённая логика расчёта расстояния
            if algorithm == "levenshtein":
                distance = fuzzy_search.levenshtein_distance(word.lower(), w.lower())  # Добавляем lower()
            elif algorithm == "ngram":
                distance = round(fuzzy_search.ngram_distance(word, w) * 10)
            else:
                continue

            results.append({"word": w, "distance": distance})

            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': int((idx + 1) / total * 100),
                    'current_word': f'{idx + 1}/{total}'
                }
            )

        # Сортируем и берём топ-10 независимо от расстояния
        sorted_results = sorted(results, key=lambda x: x["distance"])[:10]

        return {
            "execution_time": 0.0,  # Замените на реальное время выполнения
            "results": sorted_results,
            "algorithm": algorithm  # Добавляем информацию о методе
        }
    finally:
        db.close()

@celery_app.task(bind=True)
def fuzzy_search_task(self, word, algorithm, corpus_id):
    print(f"Processing task: {word}, {algorithm}, {corpus_id}")
    return {
        "results": ["test1", "test2"],
        "execution_time": 1.23
    }


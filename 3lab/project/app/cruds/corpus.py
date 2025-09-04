from sqlalchemy.orm import Session
from app.models.corpus import Corpus
from app.schemas.corpus import CorpusCreate

def create_corpus(db: Session, data: CorpusCreate):
    db_corpus = Corpus(name=data.corpus_name, text=data.text)
    db.add(db_corpus)
    db.commit()
    db.refresh(db_corpus)
    return db_corpus

def get_corpuses(db: Session):
    return db.query(Corpus).all()

def get_corpus_by_id(db: Session, corpus_id: int):
    return db.query(Corpus).filter(Corpus.id == corpus_id).first()

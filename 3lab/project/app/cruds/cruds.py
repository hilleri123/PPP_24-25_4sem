from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import Corpus, User
from app.core.hashing import get_password_hash


def create_user(db: Session, email: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def create_corpus(db: Session, corpus_name: str, text: str):
    db_corpus = Corpus(name=corpus_name, text=text)
    db.add(db_corpus)
    db.commit()
    db.refresh(db_corpus)
    return {
        "corpus_id": db_corpus.id,
        "message": "Corpus uploaded successfully"
    }


# Получение списка корпусов
def get_corpuses(db: Session):
    corpuses = db.query(Corpus).all()
    return {"corpuses": [{"id": corpus.id, "name": corpus.name} for corpus in corpuses]}


def get_corpus_by_id(db: Session, id: int):
    stmt = select(Corpus).where(Corpus.id == id)
    return db.scalar(stmt)

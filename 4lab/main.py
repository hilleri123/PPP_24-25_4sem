from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from typing import List, Optional
from datetime import datetime

# база данных и модели
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    books = relationship("Book", back_populates="author", cascade="all, delete-orphan")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    year = Column(Integer)
    author_id = Column(Integer, ForeignKey("authors.id"))
    author = relationship("Author", back_populates="books")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# схемы
class AuthorBase(BaseModel):
    name: str
class AuthorCreate(AuthorBase):
    pass
class AuthorOut(AuthorBase):
    id: int
    class Config:
        orm_mode = True
class BookBase(BaseModel):
    title: str
    year: int
    author_id: int
class BookCreate(BookBase):
    pass
class BookOut(BookBase):
    id: int
    class Config:
        orm_mode = True

app = FastAPI()

@app.get("/authors", response_model=List[AuthorOut])
def get_authors(db: Session = Depends(get_db)):
    return db.query(Author).all()

@app.post("/authors", response_model=AuthorOut, status_code=201)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    a = Author(name=author.name)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a

@app.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(404, detail="Автор не найден")
    return a

@app.put("/authors/{author_id}", response_model=AuthorOut)
def update_author(author_id: int, author: AuthorCreate, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(404, detail="Автор не найден")
    a.name = author.name
    db.commit()
    db.refresh(a)
    return a

@app.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int, db: Session = Depends(get_db)):
    a = db.query(Author).filter(Author.id == author_id).first()
    if not a:
        raise HTTPException(404, detail="Автор не найден")
    db.delete(a)
    db.commit()
    return None

@app.get("/books", response_model=List[BookOut])
def get_books(author_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Book)
    if author_id:
        q = q.filter(Book.author_id == author_id)
    return q.all()

@app.post("/books", response_model=BookOut, status_code=201)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    if book.year > datetime.now().year:
        raise HTTPException(400, detail="Год не может быть в будущем")
    author = db.query(Author).filter(Author.id == book.author_id).first()
    if not author:
        raise HTTPException(404, detail="Автор не найден")
    b = Book(title=book.title, year=book.year, author_id=book.author_id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


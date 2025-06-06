from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Session



Base = declarative_base()

class CinemaDB(Base):
    __tablename__ = "cinema"  
    
    id = Column(Integer, primary_key=True, index=True)  
    name = Column(String, nullable=False)               
    address = Column(String, nullable=False)            
    
    # Связь с фильмами (каскадное удаление)
    movies = relationship(
        "MovieDB", 
        back_populates="cinema",
        cascade="all, delete"  # Удаление всех фильмов при удалении кинотеатра
    )

class MovieDB(Base):
    __tablename__ = "movie"  
    
    
    id = Column(Integer, primary_key=True, index=True)  
    name = Column(String, nullable=False)               
    genre = Column(String, nullable=False)              
    
    # Связь с кинотеатром (внешний ключ с каскадным удалением)
    cinema_id = Column(
        Integer, 
        ForeignKey("cinema.id", ondelete="CASCADE")  # Каскадное удаление при удалении кинотеатра
    )
    
    # Обратная связь для отношения кинотеатр-фильмы
    cinema = relationship("CinemaDB", back_populates="movies")


engine = create_engine("sqlite:///./cinema.db")


Base.metadata.create_all(bind=engine)


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

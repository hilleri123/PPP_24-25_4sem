from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db(): # функция для соединения с базой данных
    db = Session() #новую сессию подключения к базе данных
    try:
        yield db
    finally:
        db.close()
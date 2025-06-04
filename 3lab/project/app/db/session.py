from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os
from app.models.user import User
from app.db.database import engine
import requests



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login/")

def get_db(): # функция для соединения с базой данных
    db = Session(bind=engine) #новую сессию подключения к базе данных
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    SECRET_KEY = os.getenv("SECRET_KEY", "Rita_key")
    ALGORITHM = "HS256"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    token = jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)
    print("Токен:", token)

    return user

from app.db.database import SessionLocal
from app.models.corpus import Corpus

def init_test_data():
    db = SessionLocal()
    try:
        if db.query(Corpus).count() == 0:
            test_corpora = [
                Corpus(
                    name="English Literature",
                    text="The quick brown fox jumps over the lazy dog."
                ),
                Corpus(
                    name="Russian Corpus",
                    text="Съешь ещё этих мягких французских булок."
                ),
                Corpus(
                    name="Technical Terms",
                    text="hello world python java javascript"
                )
            ]
            db.add_all(test_corpora)
            db.commit()
            print("Test corpora added successfully")
        else:
            print("Database already contains corpora")
    except Exception as e:
        db.rollback()
        print(f"Error initializing test data: {e}")
        raise  # Перебрасываем исключение для видимости в логах
    finally:
        db.close()
API_URL = "http://localhost:8000/user/login/"

def get_token(email: str, password: str) -> str:
    try:
        data = {
            "username": email,
            "password": password,
            "grant_type": "password"  # Необязательно, если эндпоинт не требует
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        response = requests.post(
            API_URL,
            data=data,  # Только form-data
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("access_token")  # Используйте .get() для безопасности
    except Exception as e:
        error_msg = f"Auth failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f"\nServer response: {e.response.text}"
        return None

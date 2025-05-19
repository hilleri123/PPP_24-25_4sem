from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.cruds.user import get_user_by_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # создаёт контекст для хеширования паролей

def verify_password(plain_password, hashed_password): # сравнивает введённый пароль с хешем из БД
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password): # генерирует безопасный хеш пароля
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy() #создаёт копию входных данных
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) # добавляет срок действия токена (из настроек)
    to_encode.update({"exp": expire}) # подписывает токен секретным ключом
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) # возвращает строку JWT
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # указывает endpoint для получения токена

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)): # получение текущего пользователя
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}, # добавляет заголовок WWW-Authenticate 
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) # проверяет валидность токена
        email: str = payload.get("sub") # извлекает email из payload (subject claim)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=email) # ищет пользователя в БД
    if user is None: # если что-то не так - возвращает HTTP 401 ошибку
        raise credentials_exception

    return user

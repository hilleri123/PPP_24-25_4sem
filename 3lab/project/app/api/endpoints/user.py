from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import timedelta
import os
from requests import request
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, UserWithToken, UserOut
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password
)
from app.cruds.user import get_user_by_email, create_user
from app.models.user import User

router = APIRouter(tags=["user"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login/")

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/sign-up/", response_model=UserWithToken,
             status_code=status.HTTP_201_CREATED)
async def sign_up(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    user = create_user(db, UserCreate(
        email=user_data.email,
        password=hashed_password
    ))

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=30)
    )

    return {
        "id": user.id,
        "email": user.email,
        "token": access_token
    }

@router.post("/login/")
async def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")


    return {"message": "Login successful"}

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY", "Rita_key"),
            algorithms=[os.getenv("ALGORITHM", "HS256")]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return UserOut.from_orm(user)

@router.get("/users/me/", response_model=UserOut)
async def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user

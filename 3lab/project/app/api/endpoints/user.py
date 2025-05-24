from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from fastapi.security import OAuth2PasswordBearer
from app.schemas.user import UserCreate, UserLogin, UserWithToken, UserOut
from app.core.security import create_access_token
from app.cruds import user as user_crud
import os
from jose import jwt, JWTError
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login/")


@router.post("/sign-up/", response_model=UserWithToken)
def sign_up(user_data: UserCreate, db: Session = Depends(get_db)):
    user = user_crud.get_user_by_email(db, user_data.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = user_crud.create_user(db, user_data)
    token = create_access_token({"sub": str(user.id)})
    return {"id": user.id, "email": user.email, "token": token}

@router.post("/login/", response_model=UserWithToken)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = user_crud.authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"id": user.id, "email": user.email, "token": token}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/users/me/", response_model=UserOut)
def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse, UserMeResponse
from app.schemas.brutforce import BrutHashRequest, BrutHashResponse, TaskStatusResponse
from app.cruds.user import create_user, get_user_by_email
from app.services.auth import create_access_token, get_current_user
from app.services.security import verify_password
from app.services.brutforce import start_brutforce, get_task_status
from app.db.deps import get_db
from datetime import timedelta
from app.core.config import settings
from app.models.user import User

auth_router = APIRouter()

@auth_router.post("/sign-up/", response_model=UserResponse)
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=access_token_expires
    )
    return UserResponse(id=new_user.id, email=new_user.email, token=access_token)

@auth_router.post("/login/", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == form_data.username).first()
    if not u or not verify_password(form_data.password, u.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    tkn = create_access_token(
        data={"sub": u.email},
        expires_delta=access_token_expires
    )
    return {
        "access_token": tkn,
        "token_type": "bearer",
        "id": u.id,
        "email": u.email
    }

@auth_router.get("/users/me/", response_model=UserMeResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@auth_router.post("/brut_hash", response_model=BrutHashResponse)
def brut_hash(request: BrutHashRequest):
    task_id = start_brutforce(request.hash, request.charset, request.max_length)
    return {"task_id": task_id}

@auth_router.get("/get_status", response_model=TaskStatusResponse)
def get_status(task_id: str):
    task_status = get_task_status(task_id)
    return {
        "status": task_status["status"],
        "progress": task_status["progress"],
        "result": task_status["result"]
    }

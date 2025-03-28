from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.cruds.user import get_user_by_email, create_user, verify_password
from app.schemas.user import UserCreate, UserResponse, UserInDB
from app.schemas.image import ImageRequest, ImageResponse
from app.core.security import create_access_token, verify_token
from app.services.binarization import binarize_image
from app.models.user import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
router = APIRouter()
bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials  # Извлекаем токен из credentials
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/sign-up/", response_model=UserResponse)
async def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    token = create_access_token(data={"sub": new_user.email})
    return {"id": new_user.id, "email": new_user.email, "token": token}


@router.post("/login/", response_model=UserResponse)
async def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": db_user.email})
    return {"id": db_user.id, "email": db_user.email, "token": token}


@router.get("/users/me/", response_model=UserInDB)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/binary_image", response_model=ImageResponse)
async def binary_image(request: ImageRequest, current_user: User = Depends(get_current_user)):
    binarized_image = binarize_image(request.image, request.algorithm)
    return {"binarized_image": binarized_image}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Обработка начата")
    await websocket.send_text("Обработка завершена")
    await websocket.close()

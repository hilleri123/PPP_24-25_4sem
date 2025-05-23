from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, Depends
from jwt import InvalidTokenError

from app.core.config import Config
import jwt
from app.cruds import cruds
from app.db.db import get_db
from sqlalchemy.orm import Session


def get_current_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        user_email = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = cruds.get_user_by_email(db, user_email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


def generate_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List  
from fastapi import HTTPException, status
from app.core.config import settings
import secrets
from pydantic import BaseModel


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


class TokenPayload(BaseModel):
    sub: str  
    exp: int  
    jti: str  
    scopes: List[str] = []  


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
        jti: Optional[str] = None,
        scopes: Optional[List[str]] = None  
) -> str:

    to_encode = data.copy()

    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    token_jti = jti or secrets.token_urlsafe(32)

    to_encode.update({
        "exp": expire,
        "jti": token_jti,
        "scopes": scopes or [],
        "iat": datetime.utcnow(),
        "type": "access"
    })

    try:
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token creation error: {str(e)}"
        )


def create_refresh_token(
        user_id: str,
        expires_delta: timedelta = timedelta(days=30)
) -> str:
    jti = secrets.token_urlsafe(32)
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + expires_delta,
        "jti": jti,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)

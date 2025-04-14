
from app.core.endpoints import FastApiServerInfo
from fastapi import APIRouter
import secrets
import sqlite3
from app.schemas.schemas import User

DB_PATH = "app/db/database.db"
router = APIRouter()
# Добавление нового пользователя в бд
@router.post(FastApiServerInfo.SIGN_UP_ENDPOINT)
async def sign_up(user: User):
    token, id = None, None
    existing_users = dict()
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Users WHERE email = ?", 
                   (user.email,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            id, email, password = row
            existing_user = {
                 "id": id,
                 "email": email,
             }
            existing_users[id] = existing_user
        pass
    else:
        cursor.execute("INSERT INTO Users (email, password) VALUES (?, ?)", 
                    (user.email, user.password))
        connection.commit()
        cursor.execute("SELECT id FROM Users WHERE email = ? AND password = ?", 
                    (user.email, user.password))
        id = cursor.fetchall()[0][0]
        token = secrets.token_urlsafe()
        existing_users[id] = {
                "id": id,
                "email": user.email,
                "token": token  
            }
        
    connection.close()
    return existing_users

logged_user = {
    "id": 0,
    "email": "smth"
}
@router.post(FastApiServerInfo.LOGIN_ENDPOINT)
async def login(user: User):
    token, id = None, None
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", 
                   (user.email,user.password))
    rows = cursor.fetchone()
    if rows:
        id, email, password = rows
        token = secrets.token_urlsafe()
        logged_user["id"] = id
        logged_user["email"] = email
    else:
        connection.close()
        return {"Message": "Incorrect password"}
    
    connection.close()
    return {
        "id": logged_user["id"],
        "email": logged_user["email"],
        "token": token
    }

# Вывод информации об авторизованном пользователе
@router.post(FastApiServerInfo.USER_INFO_ENDPOINT)
async def login():
    return logged_user
# import redis

# r = redis.Redis(host='localhost', port=6379, db=0)
# print(r.ping())

# import requests
#
# def test_login():
#     response = requests.post(
#         "http://localhost:8000/user/login/",
#         json={"email": "test@test.com", "password": "test"}
#     )
#     print(response.status_code)
#     print(response.text)
#
# test_login()

# from app.db.database import SessionLocal
# from app.models.corpus import Corpus
# from app.db.database import engine
#
# def check_corpora():
#     db = SessionLocal(bind=engine)
#     corpora = db.query(Corpus).all()
#     print(f"Total corpora in DB: {len(corpora)}")
#     for c in corpora:
#         print(f"ID: {c.id}, Name: {c.name}")
#     db.close()
#
# check_corpora()

# В app/db/init_db.py или при старте приложения
# from app.auth.utils import get_password_hash
# from app.models import User
# from app.db.database import SessionLocal
#
# def create_test_user():
#     db = SessionLocal()
#     if not db.query(User).filter(User.email == "test@example.com").first():
#         db_user = User(
#             email="test@example.com",
#             hashed_password=get_password_hash("testpass")
#         )
#         db.add(db_user)
#         db.commit()
#     db.close()

import requests

response = requests.post(
    "http://localhost:8000/token",
    data={
        "username": "ritusvsemogusij@gmail.com",
        "password": "Ritus_2005"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code == 200:
    print("Token:", response.json()["access_token"])
else:
    print("Error:", response.json())

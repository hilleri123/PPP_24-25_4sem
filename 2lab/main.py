# Обновляем все библиотеки
import subprocess
import sys
import os

def update_library(library_name):
    try:
        # Выполняем команду pip install --upgrade для обновления библиотеки
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", library_name])
        
        print(f"\033[32mБиблиотека '{library_name}' успешно обновлена!\033[0m")
    except subprocess.CalledProcessError as e:
        print(f"\033[31mОшибка при обновлении библиотеки '{library_name}': {e}\033[0m")
    except Exception as e:
        print(f"\033[33mПроизошла непредвиденная ошибка: {e}\033[0m")

if 0:#input('Update required libraries [y/n]?').lower() == 'y':
    
    with open('requirements.txt') as f:
        requirements = f.read().splitlines()
        
        libraries = {}
        for i in requirements:
            libraries[i.split('==')[0]] = i.split('==')[1]
        for i in libraries:
            update_library(i) 


from fastapi import FastAPI
import uvicorn
from app.core.endpoints import FastApiServerInfo
from app.api import auth
from app.api import brut



app = FastAPI(title="Практикум по программированию")

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(auth.router, tags=["Authentication"])
app.include_router(brut.router, tags=["BrutForce"])

if __name__ == "__main__":
    subprocess.run(['alembic', 'upgrade','head'])
    print(f'http://{FastApiServerInfo.IP}:{FastApiServerInfo.PORT}/docs#')
    uvicorn.run(app, host=FastApiServerInfo.IP, port=FastApiServerInfo.PORT)
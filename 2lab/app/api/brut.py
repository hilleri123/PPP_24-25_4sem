from app.core.endpoints import FastApiServerInfo
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.services.brut import *
import os
from uuid import uuid4

router = APIRouter()


TEMP_DIR = r"app\temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

tasks = {}

@router.post(FastApiServerInfo.BRUT_HASH)
async def brut_file(
    # Принимаем файл RAR-архива.
    file: UploadFile = File(...),
    charset: str = Form(...),
    max_length: int = Form(...)
):
    if max_length > 8:
        raise HTTPException(status_code=400, detail="max_length не может превышать 8")
    try:
        tasks[list(tasks.keys())[-1] + 1] = {
    "status": "running",
    "progress": 0,
    "result": "null",
    }
    except:
        tasks[1] = {
    "status": "running",
    "progress": 0,
    "result": "null",
        }
    
    # Сохраняем загруженный файл во временную директорию.
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid4()}{file_extension}"
    temp_file_path = os.path.join(TEMP_DIR, temp_filename)
    with open(temp_file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        await file.close()
    
        
    #passwords_file = 'passwords.txt'
    
    extract_rar_hash(temp_file_path.replace('\\\\','\\'))
    with open(temp_file_path.split('.')[0] + '.txt', "r") as f:
        hash_value = f.readlines()[0]

    
    generate_passwords(charset, max_length, temp_file_path.split('.')[0] + '_passwords.txt')
    found_password = brute_force_rar(temp_file_path, temp_file_path.split('.')[0] + '_passwords.txt')
    if found_password:
        tasks[list(tasks.keys())[-1]] = {
        "status": "completed",
        "progress": 100,
        "result": found_password,
        }
    else:
        tasks[list(tasks.keys())[-1]] = {
        "status": "failed",
        "progress": 100,
        "result": "null",
        }
    os.remove(temp_file_path)
    os.remove(temp_file_path.split('.')[0] + '.txt')
    os.remove(temp_file_path.split('.')[0] + '_passwords.txt')
    
    return {
        "task_id": list(tasks.keys())[-1]
    }

@router.get(FastApiServerInfo.GET_STATUS)
async def get_status(task_id: int):
    return {
        "task_id":tasks[task_id]
    }
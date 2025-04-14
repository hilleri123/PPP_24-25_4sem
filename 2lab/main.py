
def main():
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Dict
    import itertools
    
    app = FastAPI()
    
    # Модель запроса на брутфорс
    class BrutForceRequest(BaseModel):
        hash: str  # строка с хешем RAR-архива (заглушка)
        charset: str  # набор символов для генерации паролей
        max_length: int  # максимальная длина пароля
    
    # Хранилище задач (вместо базы данных для простоты)
    tasks: Dict[str, Dict] = {}
    
    @app.post("/brut_hash")
    async def brut_hash(request: BrutForceRequest):
        task_id = f"task_{len(tasks) + 1}"  # Генерация уникального id задачи
        tasks[task_id] = {
            "hash": request.hash,
            "charset": request.charset,
            "max_length": request.max_length,
            "status": "in_progress",
            "result": None,
        }
    
        # Запуск брутфорс-атаки (асинхронно)
        brute_force(request.hash, request.charset, request.max_length, task_id)
    
        return {"task_id": task_id}

    def brute_force(hash_value: str, charset: str, max_length: int, task_id: str):
        """
        Простая реализация брутфорса.
        """
        for length in range(1, max_length + 1):
            for password in itertools.product(charset, repeat=length):
                password = ''.join(password)
    
                # Заглушка проверки хеша (реальная проверка зависит от алгоритма хеширования)
                if password == hash_value:  
                    tasks[task_id]["status"] = "completed"
                    tasks[task_id]["result"] = password
                    return

        tasks[task_id]["status"] = "failed"
    
    @app.get("/tasks/{task_id}")
    async def get_task_status(task_id: str):
        """
        Получение статуса задачи по ID.
        """
        task = tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task


    pass

if __name__ == "__main__":
    main()


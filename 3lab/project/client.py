import asyncio
import json
import argparse
import getpass
import requests
from colorama import Fore, Style, init as colorama_init
import logging
from celery import Celery

colorama_init()
logging.basicConfig(level=logging.INFO, format="%(message)s")

API_URL = "http://localhost:8000"
celery_app = Celery(
    'tasks',
    broker='sqla+sqlite:///celerydb.sqlite', # очередь задач (в файле celerydb.sqlite)
    backend='db+sqlite:///results.sqlite' # хранилище результатов (в файле results.sqlite)
)
def get_token(email: str, password: str) -> str:
    response = requests.post(f"{API_URL}/auth/login/", json={"email": email, "password": password})
    response.raise_for_status()
    return response.json()["token"]

def format_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)

def color_block(label, color):
    return f"{color}{label}{Style.RESET_ALL}"

def run_celery_task(task: dict):
    task_obj = celery_app.send_task("fuzzy_search_task", args=[
        task["word"], task["algorithm"], task["corpus_id"]
    ])
    return task_obj.id

async def poll_status(task_id: str):
    while True:
        result = celery_app.AsyncResult(task_id)
        if result.successful():
            res = result.result
            if not res or res.get("results") is None or res.get("execution_time") is None:
                print(color_block("[FAILED]", Fore.RED))
                print(f"Task ID: {task_id}")
                print("Задача завершилась, но результат отсутствует. Возможно, был указан несуществующий corpus_id.")
            elif "error" in res:
                print(color_block("[ERROR]", Fore.RED))
                print(f"Task ID: {task_id}")
                print(f"Ошибка: {res['error']}")
            else:
                print(color_block("[COMPLETED]", Fore.GREEN))
                print(format_json({
                    "task_id": task_id,
                    "execution_time": res["execution_time"],
                    "results": res["results"]
                }))
            print("-" * 50)
            break
        elif result.state == "PROGRESS":
            meta = result.info or {}
            print(color_block("[PROGRESS]", Fore.BLUE), f"{meta.get('progress', 0)}% — {meta.get('current_word', '?')}")
        elif result.failed():
            print(color_block("[FAILED]", Fore.RED))
            print(f"Task failed: {result.result}")
            break
        else:
            print(color_block("[STATUS]", Fore.YELLOW), result.state)

async def run_interactive_session(token: str):
    print("\nAvailable commands: search, status, exit\n")
    while True:
        action = input("> ").strip().lower()
        if action == "exit":
            break
        elif action == "search":
            word = input("Word to search: ").strip()
            algorithm = input("Algorithm (levenshtein/ngram): ").strip()
            try:
                corpus_id = int(input("Corpus ID: ").strip())
            except ValueError:
                print(Fore.RED + "Corpus ID must be an integer." + Style.RESET_ALL)
                continue
            task = {"word": word, "algorithm": algorithm, "corpus_id": corpus_id}
            task_id = run_celery_task(task)
            print(color_block("[TASK QUEUED]", Fore.CYAN), f"Task ID: {task_id}")
            print("Use `status` command to check result.\n")
        elif action == "status":
            task_id = input("Enter Task ID: ").strip()
            await poll_status(task_id)
        else:
            print(Fore.YELLOW + "Unknown command." + Style.RESET_ALL)

def parse_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

async def run_task_sequence(tasks: list):
    for task in tasks:
        task_id = run_celery_task(task)
        print(color_block("[TASK STARTED]", Fore.CYAN), f"Task ID: {task_id}")
        await poll_status(task_id)

def main():
    parser = argparse.ArgumentParser(description="CLI Client for Fuzzy Search (Celery-based)")
    parser.add_argument("--script", help="Path to .jsonl file with search tasks")
    args = parser.parse_args()
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    try:
        token = get_token(email, password)
        print(Fore.GREEN + "Authenticated successfully." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Authentication failed: {e}" + Style.RESET_ALL)
        return
    if args.script:
        tasks = parse_file(args.script)
        asyncio.run(run_task_sequence(tasks))
    else:
        print(Fore.CYAN + "\nNo script provided. Entering interactive mode." + Style.RESET_ALL)
        asyncio.run(run_interactive_session(token))

if __name__ == "__main__":
    main()
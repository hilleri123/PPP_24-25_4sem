import asyncio
import argparse
import getpass
import requests
from colorama import Fore, Style, init as colorama_init
import logging
from app.websocket.manager import parse_file, run_task_sequence, run_interactive_session

colorama_init()
logging.basicConfig(level=logging.INFO, format="%(message)s")

API_URL = "http://localhost:8000/user/login/"

def get_token(email: str, password: str) -> str:
    try:
        # Query-параметры
        params = {
            "username": email,
            "password": password,
            "grant_type": "password"
        }

        # Form-data
        data = {
            "username": email,
            "password": password,
            "grant_type": "password"
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }


        for attempt, payload in enumerate([{"params": params}, {"data": data}]):
            try:
                response = requests.post(
                    API_URL,
                    headers=headers,
                    timeout=10,
                    **payload
                )
                response.raise_for_status()
                return response.json()["access_token"]
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                continue

        raise Exception("All authentication attempts failed")

    except Exception as e:
        print(f"[ERROR] Auth failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Server response: {e.response.text}")



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

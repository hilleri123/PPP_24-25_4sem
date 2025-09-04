import asyncio
import argparse
import getpass
from colorama import Fore, Style
from app.websocket.manager import parse_file, run_task_sequence, run_interactive_session
from app.db.session import get_token


def main():
    parser = argparse.ArgumentParser(description="CLI Client for Fuzzy Search (Celery-based)")
    parser.add_argument("--script", help="Path to .jsonl file with search tasks")
    args = parser.parse_args()
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    try:
        token = get_token(email, password)
        print(Fore.GREEN + "Authenticated successfully" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Authentication failed: {e}" + Style.RESET_ALL)
        return
    if args.script:
        tasks = parse_file(args.script)
        asyncio.run(run_task_sequence(tasks))
    else:
        asyncio.run(run_interactive_session(token))

if __name__ == "__main__":
    main()


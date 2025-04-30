import sys
from server import run_server
from client import run_client

def main():
    if len(sys.argv) < 2:
        print("python3 main.py server client")
        return

    mode = sys.argv[1].lower()
    if mode == 'server':
        run_server()
    elif mode == 'client':
        run_client()
    else:
        print("Invalid")

if __name__ == "__main__":
    main()

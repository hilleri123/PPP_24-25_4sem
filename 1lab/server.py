import socket
import threading
import json
import xml.etree.ElementTree as ET
import signal

from environment_manager import build_data_structure, update_env
from protocols import SizeProtocol
from data_serializer import dict_to_xml

HOST = 'localhost'
PORT = 65432

shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    print("\n[Server] shutdown, saving data...")
    data = build_data_structure()
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    shutdown_flag = True

# Ctrl+C и SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def handle_client(conn, addr):
    print(f"[Server] New client connected: {addr}")
    protocol = SizeProtocol(conn)

    while True:
        try:
            command = protocol.recv()
            if not command:
                break

            if command.startswith("GET "):
                fmt = command.split(" ", 1)[1].strip().upper()
                data = build_data_structure()

                if fmt == "JSON":
                    response = json.dumps(data, ensure_ascii=False, indent=2)
                elif fmt == "XML":
                    root = dict_to_xml(data, "data")
                    response = ET.tostring(root, encoding="unicode")
                else:
                    response = "ERROR: Unknown format"

                protocol.send(response)

            elif command.startswith("UPDATE_ENV "):
                # UPDATE_ENV {"MYVAR":"myval","PATH":"/usr/bin"}
                env_json = command[len("UPDATE_ENV "):].strip()
                try:
                    new_vars = json.loads(env_json)
                    update_env(new_vars)
                    protocol.send("OK")
                except Exception as e:
                    protocol.send(f"ERROR: Invalid JSON ({e})")

            elif command == "QUIT":
                protocol.send("BYE")
                break

            else:
                protocol.send("ERROR: Unknown command")

        except ConnectionResetError:
            print(f"[Server] Connection with {addr} was reset.")
            break
        except Exception as e:
            print(f"[Server] Error handling client {addr}: {e}")
            break

    conn.close()
    print(f"[Server] Client disconnected: {addr}")

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        print(f"[Server] Listening on {HOST}:{PORT}")

        while not shutdown_flag:
            try:
                s.settimeout(1.0)
                conn, addr = s.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()

        print("[Server] Shutting down server...")

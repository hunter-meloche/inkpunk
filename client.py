import socket
import os
from collections import deque
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

# Server configuration
HOST = '127.0.0.1'
PORT = 65432

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def read_credentials():
    try:
        with open('.login', 'r') as f:
            lines = f.readlines()
            username = lines[0].strip().split(': ')[1]
            password = lines[1].strip().split(': ')[1]
            return username, password
    except FileNotFoundError:
        print("Login file not found. Make sure '.login' file exists in the current directory.")
        exit()
    except IndexError:
        print("Login file format is incorrect. It should be:\nusername: your_username\npassword: your_password")
        exit()

def display_action_history(actions, username):
    clear_screen()
    print(f"Source-MUD    (User: {username})")  # Include the username in the display
    print("-----------------------------------------------")
    for _ in range(5 - len(actions)):
        print()  # Print empty line for padding
    for action in actions:
        print(action)  # Print each action
    print("-----------------------------------------------")

def main():
    actions = deque(maxlen=5)
    username, password = read_credentials()
    session = PromptSession(history=InMemoryHistory())

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"{username},{password}".encode('utf-8'))
        auth_response = s.recv(1024).decode('utf-8')
        if auth_response != "AUTH_SUCCESS":
            print("Invalid username or password. Press Enter to exit...")
            input()
            return

        print("Successfully authenticated. You can now start playing.")
        while True:
            display_action_history(actions, username)
            try:
                action = session.prompt("Enter an action ('attack', 'persuade', 'inventory', 'quit'): ").strip().lower()
            except KeyboardInterrupt:
                break

            if action == '' or action not in ['attack', 'persuade', 'inventory', 'quit']:
                print("Invalid action...")
                input("Press Enter to continue...")
                continue

            if action == 'quit':
                break

            s.sendall(action.encode('utf-8'))

            if action == 'inventory':
                inventory = s.recv(1024).decode('utf-8')  # Receive inventory from server
                print(f"Inventory: {inventory}")
                input("Press Enter to continue...")
                continue

            result = s.recv(1024).decode('utf-8')
            actions.append(f"Action: {action} - Result: {result}")


if __name__ == "__main__":
    main()

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
            outer_action = session.prompt("Enter an action ('attack', 'persuade', 'inventory', 'quit'): ").strip().lower()

            if outer_action in ['attack', 'persuade']:
                s.sendall(outer_action.encode('utf-8'))
                result = s.recv(1024).decode('utf-8')
                actions.append(f"Action: {outer_action} - Result: {result}")
            elif outer_action == 'inventory':
                s.sendall(outer_action.encode('utf-8'))
                inventory = s.recv(1024).decode('utf-8')

                while True:
                    clear_screen()  # Clear the screen before displaying the inventory
                    print("--- Inventory ---:")
                    print(inventory)
                    inventory_action = session.prompt("Inventory actions ('drop <item>', 'store <item>', 'exit'): ").strip().lower()
                    if inventory_action == 'exit':
                        print("Exiting inventory.")
                        break
                    inventory_action_parts = inventory_action.split(' ', 1)  # Splitting only on the first space.
                    if len(inventory_action_parts) == 2:
                        action, item = inventory_action_parts
                        formatted_action = f"inventory_action:{action},{item}"  # Correctly format as expected by the server
                        print(f"Sending formatted inventory action to server: {formatted_action}")  # Corrected debug print
                        s.sendall(formatted_action.encode('utf-8'))  # Send the correctly formatted action
                    else:
                        print("Invalid inventory action format.")
                        continue  # Prompt the user again for a correct action
                    response = s.recv(1024).decode('utf-8')
                    print(f"Received response from server: {response}")
                    if response not in ["Item dropped.", "Item stored."]:
                        s.sendall(outer_action.encode('utf-8'))
                        inventory = s.recv(1024).decode('utf-8')  # Wait for the updated inventory
                    else:
                        print(response) # Print the error message
            elif outer_action == 'quit':
                break

if __name__ == "__main__":
    main()

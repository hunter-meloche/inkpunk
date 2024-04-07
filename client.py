import socket
import os
from collections import deque
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style  # Import Style

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
        print_red("Login file not found. Make sure '.login' file exists in the current directory.")
        exit()
    except IndexError:
        print_red("Login file format is incorrect. It should be:\nusername: your_username\npassword: your_password")
        exit()

def print_green(text):
    print("\033[32m" + text + "\033[0m")  # Green for general text

def print_cyan(text):
    print("\033[36m" + text + "\033[0m")  # Cyan for inventory

def print_blue(text):
    print("\033[34m" + text + "\033[0m")

def print_red(text):
    print("\033[31m" + text + "\033[0m")  # Red for errors

def display_action_history(actions, username):
    clear_screen()
    print_green(f"Source-MUD    (User: {username})")
    print_green("-----------------------------------------------")
    for _ in range(5 - len(actions)):
        print()  # Print empty line for padding
    for action in actions:
        print_green(action)
    print_green("-----------------------------------------------")

def main():
    actions = deque(maxlen=5)
    username, password = read_credentials()

    # Define custom style for prompt_toolkit
    custom_style = Style.from_dict({
        '': '#00ff00',  # Set default text to green
    })

    session = PromptSession(history=InMemoryHistory(), style=custom_style)  # Apply custom style

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"{username},{password}".encode('utf-8'))
        auth_response = s.recv(1024).decode('utf-8')
        if auth_response != "AUTH_SUCCESS":
            print_red("Invalid username or password. Press Enter to exit...")
            input()
            return

        print_green("Successfully authenticated. You can now start playing.")
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
                response = ""  # Initialize response to empty string

                while True:
                    clear_screen()  # Clear the screen before displaying the inventory
                    print_cyan("--- Inventory ---")
                    print_green(inventory)
                    # If the response is not the same as inventory and is not empty, print it
                    if response != inventory and response != "":
                        # If the response starts with "Unknown inventory action:", print it in red
                        if response.startswith("Unknown inventory action:"):
                            print_red(response)
                        else:
                            print_green(response)
                    inventory_action = session.prompt("Inventory actions ('drop <item>', 'store <item>', 'exit'): ").strip().lower()
                    if inventory_action == 'exit':
                        print_green("Exiting inventory.")
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
                    # If the response does not start with "Unknown inventory action:", assign it to inventory
                    if not response.startswith("Unknown inventory action:"):
                        #s.sendall(outer_action.encode('utf-8'))
                        #inventory = s.recv(1024).decode('utf-8')  # Wait for the updated inventory
                        inventory = response
                    else:
                        continue
            elif outer_action == 'quit':
                break

if __name__ == "__main__":
    main()

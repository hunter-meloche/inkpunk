import socket
import random
import threading
import csv

# Server configuration
HOST = '127.0.0.1'
PORT = 65432

def dice_roll(dice_type):
    if dice_type == "D20":
        return random.randint(1, 20)
    elif dice_type == "D10":
        return random.randint(1, 10)

def authenticate_user(username, password, accounts):
    return any(account['username'] == username and account['password'] == password for account in accounts)

def load_accounts():
    accounts = []
    with open('accounts.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row['username']
            password = row['password']
            inventory = row['inventory'].split(';') if 'inventory' in row and row['inventory'] else []
            accounts.append({'username': username, 'password': password, 'inventory': inventory})
    return accounts

def handle_client(conn, addr, accounts):
    print(f"Connected by {addr}")
    user_inventory = []  # Placeholder for the authenticated user's inventory
    try:
        # Receive and parse login credentials
        credentials = conn.recv(1024).decode('utf-8')
        username, password = credentials.split(',')

        # Authenticate user and retrieve inventory
        for account in accounts:
            if account['username'] == username and account['password'] == password:
                conn.sendall(b"AUTH_SUCCESS")
                user_inventory = account['inventory']  # Capture the user's inventory after authentication
                break
        else:
            conn.sendall(b"AUTH_FAIL")
            return  # End connection if authentication fails

        # Main action loop
        while True:
            data = conn.recv(1024)
            if not data:
                break

            action = data.decode('utf-8').lower()
            print(f"Received action from {addr}: {action}")

            if action == "attack":
                result = dice_roll("D20")
            elif action == "persuade":
                result = dice_roll("D10")
            elif action == "inventory":
                # Join inventory items into a single string to send
                inventory_str = '; '.join(user_inventory)
                conn.sendall(inventory_str.encode('utf-8'))
                continue  # Skip the rest of the loop to wait for the next action
            else:
                result = "Unknown action"

            conn.sendall(str(result).encode('utf-8'))
            print(f"Sent result to {addr}: {result}")
    except ConnectionResetError:
        print(f"Connection with {addr} lost.")
    finally:
        conn.close()
        print(f"Connection with {addr} closed.")


def main():
    accounts = load_accounts()  # Load accounts from the CSV file

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server is listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, accounts))
            client_thread.start()
            print(f"Active connections: {threading.active_count() - 1}")

if __name__ == "__main__":
    main()

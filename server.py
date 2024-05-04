import socket
import random
import threading
import sqlite3

# Server configuration
HOST = '127.0.0.1'
PORT = 65432

def dice_roll(dice_type):
    if dice_type == "D20":
        return random.randint(1, 20)
    elif dice_type == "D10":
        return random.randint(1, 10)

def authenticate_user(username, password):
    conn = sqlite3.connect('accounts.db')
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM accounts WHERE username=? AND password=?", (username, password))
    result = cur.fetchone()
    conn.close()
    return result is not None

def load_accounts():
    conn = sqlite3.connect('accounts.db')
    cur = conn.cursor()
    cur.execute("SELECT username, password, inventory FROM accounts")
    accounts = [{'username': row[0], 'password': row[1], 'inventory': row[2].split(';') if row[2] else []} for row in cur]
    conn.close()
    return accounts

def get_user_inventory(username):
    conn = sqlite3.connect('accounts.db')
    cur = conn.cursor()
    cur.execute("SELECT inventory FROM accounts WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0].split(';') if row and row[0] else []

def update_inventory(username, inventory):
    inventory_str = ';'.join(inventory)
    conn = sqlite3.connect('accounts.db')
    cur = conn.cursor()
    cur.execute("UPDATE accounts SET inventory=? WHERE username=?", (inventory_str, username))
    conn.commit()
    conn.close()

def handle_inventory_actions(action, item, user_inventory):
    if action == "drop":
        if item in user_inventory:
            user_inventory.remove(item)
            return True, "Item dropped."
        else:
            return False, "Item not found."
    elif action == "store":
        user_inventory.append(item)
        return True, "Item stored."
    return False, f"Unknown inventory action: {action}"

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    authenticated_username = None

    try:
        credentials = conn.recv(1024).decode('utf-8')
        username, password = credentials.split(',')

        if authenticate_user(username, password):
            conn.sendall(b"AUTH_SUCCESS")
            authenticated_username = username
        else:
            conn.sendall(b"AUTH_FAIL")
            return

        while True:
            data = conn.recv(1024)
            if not data:
                break

            action = data.decode('utf-8').lower()
            if action == "attack":
                result = dice_roll("D20")
            elif action == "persuade":
                result = dice_roll("D10")
            elif action == "inventory" and authenticated_username:
                user_inventory = get_user_inventory(authenticated_username)
                inventory_str = '; '.join(user_inventory)
                conn.sendall(inventory_str.encode('utf-8'))
                continue
            elif "inventory_action" in action and authenticated_username:
                _, action_details = action.split(':')
                command, item = action_details.split(',')
                success, message = handle_inventory_actions(command, item, user_inventory)

                if not success:
                    conn.sendall(message.encode('utf-8'))
                    continue

                update_inventory(authenticated_username, user_inventory)
                inventory_str = '; '.join(user_inventory)
                conn.sendall(inventory_str.encode('utf-8'))
                continue
            else:
                result = "Unknown action"
            conn.sendall(str(result).encode('utf-8'))
    except ConnectionResetError:
        print(f"Connection with {addr} lost.")
    finally:
        conn.close()
        print(f"Connection with {addr} closed.")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server is listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
            print(f"Active connections: {threading.active_count() - 1}")

if __name__ == "__main__":
    main()

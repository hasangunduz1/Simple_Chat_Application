# -*- coding: utf-8 -*-
import socket
import threading

clients = {}
usernames = {}

def handle_client(client_socket, addr):
    try:
        username = client_socket.recv(1024).decode()
        usernames[client_socket] = username
        clients[username] = client_socket
        print(f"{username} ({addr}) connected.")

        while True:
            msg = client_socket.recv(4096).decode()
            if msg.startswith("TO:"):
                _, to_user, message = msg.split(":", 2)
                if to_user in clients:
                    full_message = f"{usernames[client_socket]}: {message}"
                    clients[to_user].send(full_message.encode())
            else:
                continue
    except:
        print(f"{usernames.get(client_socket, addr)} disconnected.")
        if client_socket in usernames:
            del clients[usernames[client_socket]]
            del usernames[client_socket]
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 5555))
    server.listen(5)
    print("Server is listening on port 5555...")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()

if __name__ == "__main__":
    start_server()

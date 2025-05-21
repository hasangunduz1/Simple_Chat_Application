# -*- coding: utf-8 -*-
import socket
import threading
import customtkinter as ctk
import os
import sys

HOST = 'localhost'
PORT = 5555

ctk.set_appearance_mode("dark")  # Dark mode
ctk.set_default_color_theme("dark-blue")

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.username = self.prompt_username()
        if not self.username:
            sys.exit()
        self.root.title(f"Simple Chat App - {self.username}")
        self.selected_user = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.setup_ui()
        self.connect_to_server()

    def prompt_username(self):
        return ctk.CTkInputDialog(text="Please enter your username:", title="Username").get_input()

    def setup_ui(self):
        self.root.geometry("800x600")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Left panel - user list
        self.user_listbox_frame = ctk.CTkFrame(self.root, width=200)
        self.user_listbox_frame.grid(row=0, column=0, sticky="nswe", padx=5, pady=5)
        self.user_listbox_frame.grid_rowconfigure(1, weight=1)

        title_label = ctk.CTkLabel(self.user_listbox_frame, text="People", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=0, column=0, pady=(10,0), padx=10)

        self.user_listbox = ctk.CTkScrollableFrame(self.user_listbox_frame)
        self.user_listbox.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)
        self.user_listbox.grid_columnconfigure(0, weight=1)

        self.exit_button = ctk.CTkButton(self.user_listbox_frame, text="Log Out", fg_color="#e74c3c", hover_color="#c0392b", command=self.quit_app)
        self.exit_button.grid(row=2, column=0, pady=10, padx=10, sticky="we")

        # Right panel - chat area
        self.chat_frame = ctk.CTkFrame(self.root)
        self.chat_frame.grid(row=0, column=1, sticky="nswe", padx=5, pady=5)
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_scroll = ctk.CTkScrollableFrame(self.chat_frame)
        self.chat_scroll.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.chat_scroll.grid_columnconfigure(0, weight=1)

        # Entry and send button frame
        bottom_frame = ctk.CTkFrame(self.chat_frame)
        bottom_frame.grid(row=1, column=0, sticky="we", padx=10, pady=(0,10))
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(bottom_frame, font=ctk.CTkFont(size=14))
        self.entry.grid(row=0, column=0, sticky="we", padx=(0, 10))
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.send_btn = ctk.CTkButton(bottom_frame, text="Send", fg_color="#25d366", hover_color="#1ebe57", command=self.send_message)
        self.send_btn.grid(row=0, column=1)

        self.load_users()

    def load_users(self):
        # Clear existing buttons
        for widget in self.user_listbox.winfo_children():
            widget.destroy()

        if not os.path.exists("users.txt"):
            open("users.txt", "w").close()

        with open("users.txt", "r", encoding="utf-8") as f:
            users = f.read().splitlines()

        if self.username not in users:
            users.append(self.username)
            with open("users.txt", "a", encoding="utf-8") as f:
                f.write(self.username + "\n")

        # Add buttons for other users
        for user in users:
            if user == self.username:
                continue
            btn = ctk.CTkButton(self.user_listbox, text=user, width=150, command=lambda u=user: self.select_user(u))
            btn.pack(pady=5, padx=10, fill="x")

    def select_user(self, user):
        self.selected_user = user
        self.load_chat(user)

    def load_chat(self, user):
        self.clear_chat()
        file_name = f"chats/{'_'.join(sorted([self.username, user]))}.txt"
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                for line in f:
                    self.add_message(line.strip(), sent_by_me=line.startswith("Me:"))

    def clear_chat(self):
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()

    def add_message(self, text, sent_by_me=False):
        msg_label = ctk.CTkLabel(
            self.chat_scroll,
            text=text,
            fg_color="#25d366" if sent_by_me else "#444444",
            text_color="white",
            corner_radius=15,
            wraplength=400,
            font=ctk.CTkFont(size=16),
            justify="left" if not sent_by_me else "right",
            anchor="w"
        )
        msg_label.pack(anchor="e" if sent_by_me else "w", pady=5, padx=10)
        self.chat_scroll.update_idletasks()
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        for child in self.chat_scroll.winfo_children():
            if child.winfo_class() == 'Canvas':
                child.yview_moveto(1.0)
                break

    def connect_to_server(self):
        try:
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(self.username.encode())
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            ctk.CTkMessageBox(title="Connection Error", message=str(e)).show()
            self.root.quit()

    def receive_messages(self):
        while True:
            try:
                msg = self.client_socket.recv(4096).decode()
                sender, content = msg.split(":", 1)
                if sender == self.selected_user:
                    self.add_message(f"{sender}: {content}", sent_by_me=False)

                    filename = f"chats/{'_'.join(sorted([self.username, sender]))}.txt"
                    os.makedirs("chats", exist_ok=True)
                    with open(filename, "a", encoding="utf-8") as f:
                        f.write(f"{sender}: {content}\n")
            except:
                break

    def send_message(self):
        message = self.entry.get()
        if not self.selected_user:
            ctk.CTkMessageBox(title="Target Selection", message="Please select a user to chat with.").show()
            return
        if message.strip() == "":
            return
        try:
            full_msg = f"TO:{self.selected_user}:{message}"
            self.client_socket.send(full_msg.encode())

            self.add_message(f"Me: {message}", sent_by_me=True)
            self.entry.delete(0, "end")

            filename = f"chats/{'_'.join(sorted([self.username, self.selected_user]))}.txt"
            os.makedirs("chats", exist_ok=True)
            with open(filename, "a", encoding="utf-8") as f:
                f.write(f"Me: {message}\n")
        except Exception as e:
            ctk.CTkMessageBox(title="Sending Error", message=str(e)).show()

    def quit_app(self):
        try:
            self.client_socket.close()
        except:
            pass
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatClient(root)
    root.mainloop()

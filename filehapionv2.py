import os
import random
import string
import socket
import threading
from tkinter import Tk, Label, Button, Entry, messagebox, Listbox, MULTIPLE

# Shared folder for the server
SHARED_FOLDER = "shared_files"
HOST = '0.0.0.0'  # Server listens on all network interfaces
PORT = 5000


# --- Server Functionality ---
def generate_connection_code():
    """Generate a unique connection code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def handle_client(client_socket, client_address):
    """Handle communication with a connected client."""
    print(f"[INFO] Connection established with {client_address}")

    try:
        # Send a welcome message and connection code
        client_socket.send(f"Connected to server. You can now browse and download files.\n".encode())

        # Handle client commands
        while True:
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break

            if command == "LIST":
                # List files in the shared folder
                files = os.listdir(SHARED_FOLDER)
                response = "\n".join(files) if files else "No files available."
                client_socket.send(response.encode())

            elif command.startswith("DOWNLOAD"):
                # Handle file download request
                _, filename = command.split(" ", 1)
                file_path = os.path.join(SHARED_FOLDER, filename)
                if os.path.exists(file_path):
                    # Send the file size
                    file_size = os.path.getsize(file_path)
                    client_socket.send(f"SIZE {file_size}".encode())
                    ack = client_socket.recv(1024).decode()  # Wait for client acknowledgment

                    # Send the file content
                    with open(file_path, "rb") as f:
                        while chunk := f.read(1024):
                            client_socket.send(chunk)
                    print(f"[INFO] File '{filename}' sent to {client_address}")
                else:
                    client_socket.send("ERROR File not found.".encode())

            elif command == "EXIT":
                # Disconnect the client
                client_socket.send("Goodbye!".encode())
                break

            else:
                client_socket.send("ERROR Invalid command.".encode())

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        client_socket.close()
        print(f"[INFO] Connection with {client_address} closed.")


def start_server():
    """Start the file-sharing server."""
    if not os.path.exists(SHARED_FOLDER):
        print(f"[ERROR] The shared folder '{SHARED_FOLDER}' does not exist.")
        print("Please manually create the folder in the same directory as this script and try again.")
        return

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    connection_code = generate_connection_code()
    print(f"[INFO] Server started on {HOST}:{PORT}")
    print(f"[INFO] Connection Code: {connection_code}")
    print(f"[INFO] Shared Folder: {os.path.abspath(SHARED_FOLDER)}")

    while True:
        client_socket, client_address = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()


# --- Client Functionality ---
def get_desktop_path():
    """Get the user's desktop path."""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def connect_to_server(server_ip, file_listbox, download_button):
    """Connect to the file-sharing server and update the GUI with the file list."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, PORT))
        print(client.recv(1024).decode())  # Welcome message from server

        # Request the file list
        client.send("LIST".encode())
        file_list = client.recv(1024).decode().split("\n")

        # Update the GUI with the file list
        file_listbox.delete(0, "end")
        for file in file_list:
            file_listbox.insert("end", file)

        # Enable the download button
        download_button.config(state="normal")

        return client
    except Exception as e:
        messagebox.showerror("Connection Error", f"Failed to connect to the server: {e}")
        return None


def download_files(client, selected_files):
    """Download the selected files from the server to the Desktop."""
    desktop_path = get_desktop_path()
    try:
        for file in selected_files:
            # Send the download command
            client.send(f"DOWNLOAD {file}".encode())
            response = client.recv(1024).decode()
            if response.startswith("SIZE"):
                # File size received
                file_size = int(response.split(" ")[1])
                client.send("READY".encode())  # Acknowledge file size

                # Receive file content
                file_save_path = os.path.join(desktop_path, file)
                with open(file_save_path, "wb") as f:
                    received_size = 0
                    while received_size < file_size:
                        chunk = client.recv(1024)
                        f.write(chunk)
                        received_size += len(chunk)
                print(f"[INFO] File '{file}' downloaded successfully to {desktop_path}.")
            else:
                print(f"[ERROR] {response}")
        messagebox.showinfo("Download Complete", f"Selected files have been downloaded to your Desktop.")
    except Exception as e:
        messagebox.showerror("Download Error", f"Failed to download files: {e}")


# --- Main Menu ---
def main_menu():
    def start_sharing():
        threading.Thread(target=start_server, daemon=True).start()

    def connect_to_sharing():
        server_ip = ip_entry.get()
        if not server_ip:
            messagebox.showerror("Error", "Please enter the server IP address.")
        else:
            client = connect_to_server(server_ip, file_listbox, download_button)
            if client:
                connected_clients.append(client)

    def download_selected_files():
        selected_files = [file_listbox.get(i) for i in file_listbox.curselection()]
        if not selected_files:
            messagebox.showwarning("No Files Selected", "Please select at least one file to download.")
            return
        if connected_clients:
            download_files(connected_clients[0], selected_files)

    connected_clients = []

    root = Tk()
    root.title("FileHapion")
    root.geometry("500x500")
    root.configure(bg="black")

    # ASCII Art Title
    ascii_art = """
    ███████╗██╗██╗      ███████╗██╗  ██╗ █████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
    ██╔════╝██║██║      ██╔════╝██║  ██║██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║
    █████╗  ██║██║      █████╗  ███████║███████║██████╔╝██║██║   ██║██╔██╗ ██║
    ██╔══╝  ██║██║      ██╔══╝  ██╔══██║██╔══██║██╔═══╝ ██║██║   ██║██║╚██╗██║
    ██║     ██║███████╗ ███████╗██║  ██║██║  ██║██║     ██║╚██████╔╝██║ ╚████║
    ╚═╝     ╚═╝╚══════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
    """
    Label(root, text=ascii_art, font=("Courier", 10), bg="black", fg="cyan").pack(pady=10)

    Label(root, text="File Sharing Program", font=("Helvetica", 16), bg="black", fg="yellow").pack(pady=10)

    Button(root, text="Start Sharing Files", font=("Helvetica", 12), bg="green", fg="white", command=start_sharing).pack(pady=10)

    Label(root, text="Enter Server IP to Connect:", font=("Helvetica", 12), bg="black", fg="yellow").pack(pady=10)
    ip_entry = Entry(root, font=("Helvetica", 12), width=30)
    ip_entry.pack(pady=5)

    Button(root, text="Connect to Shared Files", font=("Helvetica", 12), bg="blue", fg="white", command=connect_to_sharing).pack(pady=10)

    Label(root, text="Available Files:", font=("Helvetica", 12), bg="black", fg="yellow").pack(pady=10)
    file_listbox = Listbox(root, selectmode=MULTIPLE, font=("Helvetica", 12), width=40, height=10)
    file_listbox.pack(pady=10)

    download_button = Button(root, text="Download Selected Files", font=("Helvetica", 12), bg="purple", fg="white", command=download_selected_files, state="disabled")
    download_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main_menu()
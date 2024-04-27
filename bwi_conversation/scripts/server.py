import socket
import threading

data=None

def handle_client(client_socket):
    # Receive data from the client
    global data 
    data = client_socket.recv(1024)  # Adjust buffer size as needed
    print(f"Received: {data.decode()} from {client_socket.getpeername()}")
    data = data.decode()
    # Close the connection
    client_socket.close()

def generate_data():
    global data
    return data

def start_server(port):
    global data
    # Define host
    HOST = '10.0.0.145'  # Use 0.0.0.0 to listen on all available interfaces

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_socket.bind((HOST, port))

    # Listen for incoming connections
    server_socket.listen()

    print(f"Server listening on {HOST}:{port}")

    while True:
        # Accept incoming connections
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")

        # Handle the client in a separate thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()


# If you want to start the server immediately when this script is run,
# you can call start_server with a specific port
if __name__ == "__main__":
    start_server(12345)  # Change the port number as needed

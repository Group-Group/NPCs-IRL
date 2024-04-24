import socket

# Define host and port
HOST = '10.0.0.145'  # Use 0.0.0.0 to listen on all available interfaces
PORT = 12345      # Choose a port (e.g., 12345)

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()

print(f"Server listening on {HOST}:{PORT}")

# Accept incoming connections
client_socket, client_address = server_socket.accept()
print(f"Connection from {client_address}")

# Receive data from the client
data = client_socket.recv(1024)  # Adjust buffer size as needed
print("Received:", data.decode())

# Close the connection
client_socket.close()
server_socket.close()

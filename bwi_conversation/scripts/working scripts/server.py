import socket

# Define host and port
HOST = '10.0.0.145'  # Use 0.0.0.0 to listen on all available interfaces
PORT = 12345      # Choose a port (e.g., 12345)
PORT2 = 23456

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_socket.bind((HOST, PORT))
server_socket2.bind((HOST, PORT2))

# Listen for incoming connections
server_socket.listen()
server_socket2.listen()

print(f"Server listening on {HOST}:{PORT}")
print(f"Server listening on {HOST}:{PORT2}")


# Accept incoming connections
client_socket, client_address = server_socket.accept()
client_socket2, client_address2 = server_socket2.accept()
print(f"Connection from {client_address}")

# Receive data from the client
data = client_socket.recv(1024)  # Adjust buffer size as needed
data2 = client_socket2.recv(2048)  # Adjust buffer size as needed
print("Received:", data.decode())
print("Received2:", data2.decode())

# Close the connection
client_socket.close()
client_socket2.close()
server_socket.close()
server_socket2.close()


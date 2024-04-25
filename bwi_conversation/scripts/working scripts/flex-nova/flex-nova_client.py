import socket

# Define server address and port
SERVER_HOST = '10.0.0.145'  # Replace with the server's IP address
SERVER_PORT = 23456                # Replace with the server's port

# Create a socket object    
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((SERVER_HOST, SERVER_PORT))

# Send data to the server
message = "Hello, server!"
client_socket.send(message.encode())

# Close the connection
client_socket.close()

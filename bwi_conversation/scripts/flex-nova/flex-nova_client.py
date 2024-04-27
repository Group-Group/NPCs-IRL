import socket
import json

# Define server address and port
SERVER_HOST = '10.0.0.145'  # Replace with the server's IP address
SERVER_PORT = 23456                # Replace with the server's port

# Create a socket object    
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
client_socket.connect((SERVER_HOST, SERVER_PORT))

robot_x = 5
robot_y = 0
# Send data to the server
message = [robot_x, robot_y]

data = json.dumps(message)
client_socket.sendall(data.encode())

response = client_socket.recv(1024).decode()
print("Response from server:", response)

# Close the connection
client_socket.close()

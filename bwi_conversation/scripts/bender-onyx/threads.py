import roslibpy
import roslibpy.tf
import threading
import socket
import json
import math
import time

HOST = '10.0.0.145'
PORT = 23478

PROXIMITY_METERS = 2


class ClientThreadHandle:
    """
    ThreadHandle handles the client socket and ROS. 
    ### Attributes
    * last_response_from_server
    """
    def __init__(self, client):
        self.rh = ROSLocationHandle(client) # ros handle
        self.last_response_from_server = None
        self.thread = threading.Thread(target=self.send_pos_to_server)
        self.thread.start()

    def send_pos_to_server(self):
        while True:
            x, y = self.rh.get_location()
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST, PORT))
            message = json.dumps([x, y])
            client_socket.sendall(message.encode())

            # receive the servers response
            response = client_socket.recv(1024).decode()
            self.last_response_from_server = response
            print(f"Response from server: {response}")

            client_socket.close()
            time.sleep(0.5)

class ServerThreadHandle:
    """
    SeverThreadHandle handles the server socket and ROS. 
    ### Attributes
    * last_message_sent
    """
    def __init__(self, client):
        self.rh = ROSLocationHandle(client) # ros handle
        self.last_message_sent = None
        self.last_location_seen = None

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        self.server_socket = server_socket
        print(f"Server listening on {HOST}:{PORT}")

        thread = threading.Thread(target=self.run_server)
        thread.start()
        self.thread = thread

    def run_server(self):
        while True:
            client_socket, client_addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr))
            client_thread.start()
    
    def handle_client(self, client_socket, client_addr):
        # print(f"Connection from {client_addr}")
        data = client_socket.recv(1024)
        other_robot_pos = json.loads(data.decode())
        other_robot_pos = (other_robot_pos[0], other_robot_pos[1])
        self.last_location_seen = other_robot_pos

        # send a message back to client when in range
        if math.dist(self.rh.get_location(), other_robot_pos) < PROXIMITY_METERS:
            print("IN RANGE")
            response_message = "conversation started"
            self.last_message_sent = response_message
            client_socket.sendall(response_message.encode())
        
        # print(f"Connection with {client_addr} closed")
        client_socket.close()

class ROSLocationHandle:
    def __init__(self, client):
        # client is a roslibpy.Ros object
        self.x = 0
        self.y = 0

        # subscribe to the robot's position
        self.tf_client = roslibpy.tf.TFClient(client, "/2ndFloorWhole_map")
        self.tf_client.subscribe("base_link", self.callback)

    def callback(self, msg):
        self.x = msg['translation']['x']
        self.y = msg['translation']['y']

    def get_location(self):
        return (self.x, self.y)
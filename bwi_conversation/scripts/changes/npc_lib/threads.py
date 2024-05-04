import roslibpy
import roslibpy.tf
import threading
import socket
import json
import math
import time

HOST = '10.0.0.140'
PORT = 23485

PROXIMITY_METERS = 2.5

class ClientThread:
    """
    `ClientThreadHandle` handles the client thread and ROS. 
    ### Attributes
    * `last_response_from_server`
    """
    def __init__(self, client):
        self.rh = ROSLocationHandle(client) # ros handle
        self.last_response_from_server = None

        # connect to ROS location server
        client = Client()
        client.connect_to_server()
        print("Connected to ROS location server.")
        self.client = client
        self.client_socket = client.client_socket
        self.send_far = False

        thread = threading.Thread(target=self.send_pos_to_server)
        thread.start()

    def send_pos_to_server(self):
        while True:
            x, y = self.rh.get_location()
            if self.send_far:
                x, y = [-1000, -1000]
            message = json.dumps([x, y])
            print(message + "sending")
            self.client_socket.sendall(message.encode())

            # receive the servers response
            print("Location response waiting")
            encoded_response = self.client_socket.recv(1024)
            print("Got Locations")
            response = encoded_response.decode()
            self.last_response_from_server = response
            print(f"Response from server: {response}")

            time.sleep(0.5)

class ServerThread:
    """
    `SeverThreadHandle` handles the server thread and ROS. 
    ### Attributes
    * `last_message_sent`
    * `last_location_seen`
    """
    def __init__(self, client):
        self.rh = ROSLocationHandle(client) # ros handle
        self.last_location_seen = None # location of other robot (x, y, z, w)
        self.last_message_sent = None

        # start the ROS location server
        server = Server()
        server.start_server()
        self.server = server
        self.server_socket = server.server_socket

        thread = threading.Thread(target=self.run_server)
        thread.start()

    def run_server(self):
        while True:
            client_socket, client_addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr))
            client_thread.start()
    
    def handle_client(self, client_socket, client_addr):
        while True:
            print(f"Connection from {client_addr}")
            data = client_socket.recv(1024)
            x, y = json.loads(data.decode())
            print(f"Received coordinates from client: ({x}, {y})")
            self.last_location_seen = (x, y, 0.217, 1.0)

            # send a message back to client when in range
            if math.dist(self.rh.get_location(), (x, y)) < PROXIMITY_METERS:
                print("IN RANGE")
                response_message = "conversation started"
                self.last_message_sent = response_message
            else:
                response_message = ""
            client_socket.sendall(response_message.encode())

        
        # print(f"Connection with {client_addr} closed")
        # client_socket.close()

class Client:
    """
    `ClientHandle` handles starting and stopping the client socket.
    ### Methods
    * `connect_to_server`
    * `close_connection_to_server`

    ### Attributes
    * `client_socket`
    """
    def __init__(self):
        self.client_socket = None
    
    def connect_to_server(self, host=HOST, port=PORT, timeout=float('inf')):
        start = time.time()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        while time.time() - start < timeout:
            try:
                client_socket.connect((host, port))
                print("Connected to server successfully!")
                self.client_socket = client_socket
                return
            except ConnectionRefusedError:
                print("Connection refused. Retrying in 0.5 seconds...")
                time.sleep(0.5)

        raise TimeoutError(
            f"Request to connect to server (host={host}, port={port}) timed out.")

    def close_connection_to_server(self):
        self.client_socket.close()

class Server:
    """
    `ServerHandle` handles starting and stopping the server socket
    ### Methods
    * `start_server`
    * `stop_server`

    ### Attributes
    * `server_socket`
    """
    def __init__(self):
        self.server_socket = None
    
    def start_server(self, host=HOST, port=PORT):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen()
        self.server_socket = server_socket
        print(f"Server listening on {host}:{port}")

    def stop_server(self):
        print("Stopping server")
        self.server_socket.shutdown()
        self.server_socket.close()

class ROSLocationHandle:
    def __init__(self, client):
        # client is a roslibpy.Ros object
        self.x = -1000
        self.y = -1000

        # subscribe to the robot's position
        self.tf_client = roslibpy.tf.TFClient(client, "/2ndFloorWhole_map")
        self.tf_client.subscribe("base_link", self.callback)

    def callback(self, msg):
        # print(str(msg['translation']['x']) + " " + str(msg['translation']['y']))
        self.x = msg['translation']['x']
        self.y = msg['translation']['y']

    def get_location(self):
        return (self.x, self.y)
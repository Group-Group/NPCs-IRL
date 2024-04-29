import roslibpy
import roslibpy.actionlib
import pykinect_azure as pykinect
import time
import platform
import os
import random
from openai import OpenAI
from pathlib import Path
import roslibpy.tf
import socket
import threading
import json
from mutagen.mp3 import MP3
import math

last_destination = None
incomplete_action = False

AIc = OpenAI(
    # This is the default and can be omitted
    api_key="sk-proj-98CEKi821xDabqz4Lmi1T3BlbkFJWLZVBqJ15e7eqBxCwZCR",
)

with open("conversation.txt", "w") as file:
    file.write("")
    file.close()

def text_to_audio(text, language='en'):

    speech_file_path = Path(__file__).parent / "output.mp3"
    response = AIc.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )

    response.stream_to_file(speech_file_path)


    if platform.system() == 'Windows':
        os.system("start output.mp3")
    elif platform.system() == 'Darwin':
        os.system("afplay output.mp3")
    else:  # Linux
        os.system("mpg123 output.mp3") 

waiting_for_response = False
generating_response = True
ready_to_send = False
got_response = False
response = None
response_received = None

def converse():
    global waiting_for_response, generating_response, ready_to_send, response, response_received, got_response, in_convo
    with open("conversation.txt", "r") as file:
        convo = file.read()
        file.close()
    if generating_response:
        if convo == "":
            generated_response = AIc.chat.completions.create(
            messages=[
                    {
                        "role": "user",
                        "content": "You are a BWI robot, circiling the robotics lab and ran into a person and they started talking to you. Respond to them with a casual greeting and reply to them if needed. Only write your response.",
                    }
                ],
                model="gpt-3.5-turbo",
            )

            response = generated_response.choices[0].message.content
        else:
            generated_response = AIc.chat.completions.create(
            messages=[
                    {
                        "role": "user",
                        "content": "You are a BWI robot, currently in a casual conversation with a person. The conversation so far has been \"" + convo + "\". They just said \"" + response_received + "\". Respond to them with a casual conversational response. Only write your response.",
                    }
                ],
                model="gpt-3.5-turbo",
            )

            response = generated_response.choices[0].message.content
        text_to_audio(response)
        audio = MP3("output.mp3")
        time.sleep(audio.info.length)
        ready_to_send = True
        waiting_for_response = True
        generating_response = False
        if convo == "":
            with open("conversation.txt", "a") as file:
                file.write("Robot: " + response)
                file.close()
        else:
            with open("conversation.txt", "a") as file:
                file.write("\nOther Robot: " + response_received + "\nRobot: " + response)
                file.close()
    else:
        while not got_response:
            continue
        if "Goodbye" in response_received:
            in_convo = False
            waiting_for_response = False
            generating_response = True
            ready_to_send = False
            got_response = False
            response = None
            response_received = None
            with open("conversation.txt", "w") as file:
                file.write("")
                file.close()
        
        got_response = False
        generating_response = True
        waiting_for_response = False
        converse()


client = roslibpy.Ros(host="0.0.0.0", port=9090)
client.run()
print("IS ROS CONNECTED ", client.is_connected)

action_client = roslibpy.actionlib.ActionClient(
    client, "/move_base", "move_base_msgs/MoveBaseAction" )

# target is (x, y, quat z, quat w)
def go_to_pos(target):
    global move_goal

    print("going to position " + str(target))
    message = {
        "target_pose": {
            "header": {"frame_id": "level_mux_map"},
            "pose": {
                "position": {"x": positions[target][0], "y": positions[target][1], "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": positions[target][2], "w": positions[target][3]},
            },
        }
    }

    move_goal = roslibpy.actionlib.Goal(action_client, message)
    move_goal.send()

    #TODO Body Detection more accurately
    while move_goal is not None and not move_goal.is_finished:
        if in_convo:
            converse()
        continue
    if in_convo:
        converse()

def cancel_goal():
    
    global move_goal
    if move_goal is not None:
        print("move goal cancelled")
        move_goal.cancel()
        move_goal = None


time_unavailable = time.time()

other_robot_pos = [-100000, -10000]

robot_x = -100000
robot_y = -100000
# Function to handle client connections
def handle_client(client_socket, client_address):
    global other_robot_pos, waiting_for_response, generating_response, ready_to_send, response, response_received, got_response, in_convo, time_unavailable
    print(f"Connection from {client_address}")
    data = client_socket.recv(1024)
    if not in_convo and data:

        other_robot_pos = json.loads(data.decode())
    
    # Send a message back to the client
    if math.sqrt(pow(robot_x - other_robot_pos[0], 2) + pow(robot_y - other_robot_pos[1], 2)) < 2 and time_unavailable < time.time():
        print("WITHIN RANGE")
        response_message = "conversation started"
        client_socket.sendall(response_message.encode())
        time_unavailable = time.time() + 1000
        cancel_goal_with_timeout()
    elif in_convo:
        print("running?")
        current_status = data.decode()
        if waiting_for_response:
            if "generating response" in current_status:
                response_message = "waiting for response"
                client_socket.sendall(response_message.encode())
            else:
                print(current_status)
                waiting_for_response = False
                response_received = current_status
                generating_response = True
                got_response = True
                ready_to_send = False

            client_socket.close()
        elif not ready_to_send:
            print("generating response")
            response_message = "generating response"
            client_socket.sendall(response_message.encode())

            client_socket.close()
        elif ready_to_send:
            client_socket.sendall(response.encode())
            ready_to_send = False
            waiting_for_response = True

            client_socket.close()

    else:
    # Close the connection
        client_socket.close()
    print(f"Connection with {client_address} closed")


# Define host and port
HOST = '10.0.0.145'  # Use 0.0.0.0 to listen on all available interfaces
PORT = 34562     # Choose a port (e.g., 12345)

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()

print(f"Server listening on {HOST}:{PORT}") 

# Function to run the server loop
def run_server():
    while True:
        # Accept incoming connections
        client_socket, client_address = server_socket.accept()
        # Handle the client connection in a separate thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

# Start the server loop in a separate thread
server_thread = threading.Thread(target=run_server)
server_thread.start()


def pose_callback(message):
   global robot_x, robot_y
   robot_x = message['translation']['x']
   robot_y = message['translation']['y']
#    print("my_x: " + str(robot_x) + "  my_y: " + str(robot_y))




# Subscribe to the robot's pose topic]
tf_client = roslibpy.tf.TFClient(client, "/2ndFloorWhole_map")
tf_client.subscribe("base_link", pose_callback)

def send_data():
   while True:
       global robot_x, robot_y
       tf_client.subscribe("base_link", pose_callback)
       time.sleep(0.5)

send_data_thread = threading.Thread(target=send_data)
send_data_thread.start()

positions = {
    "tv_screen": [-0.424, 6.777, 0.217, 1.0],
    "coffee_table": [-0.619, -0.202, 0.217, 1.0]
}

in_convo = False

def cancel_goal_with_timeout():
    global move_goal, in_convo
    if move_goal is not None:
        in_convo = True
        move_goal.cancel()
        move_goal = None
        


while True:
    if in_convo:
        converse()
    if incomplete_action:
        incomplete_action = False
        go_to_pos(last_destination)
    keys_list = [key for key in positions.keys() if key != last_destination] # make sure this works TODO
    random_position = random.choice(keys_list) # could make it so it excludes last destination key
    if random_position != last_destination:
        last_destination = random_position
        go_to_pos(random_position)


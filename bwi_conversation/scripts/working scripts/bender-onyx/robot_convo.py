import roslibpy
import roslibpy.actionlib
import cv2
import pykinect_azure as pykinect
import time
import speech_recognition as sr
import platform
import os
import random
from openai import OpenAI
from pathlib import Path
import roslibpy.tf
import socket
import threading
import json
import math

last_destination = None
incomplete_action = False

pykinect.initialize_libraries(module_k4abt_path='/usr/lib/libk4abt.so', track_body=False)

# Modify camera configuration
device_config = pykinect.default_configuration
device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P

# Start device
device = pykinect.start_device(config=device_config)

AIc = OpenAI(
    # This is the default and can be omitted
    api_key="sk-proj-98CEKi821xDabqz4Lmi1T3BlbkFJWLZVBqJ15e7eqBxCwZCR",
)

with open("conversation.txt", "w") as file:
    file.write("")
    file.close()

def recognize_speech():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        print("Processing...")
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand audio.")
        return None
    except sr.RequestError as e:
        print("Error occurred during request to Google Speech Recognition service:", str(e))
        return None

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


def converse():
    with open("conversation.txt", "r") as file:
        convo = file.read()
        file.close()
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
                    "content": "You are a BWI robot, currently in a casual conversation with a person. The conversation so far has been \"" + convo + "\". They just said \"" + recognized_text + "\". Respond to them with a casual conversational response. Only write your response.",
                }
            ],
            model="gpt-3.5-turbo",
        )

        response = generated_response.choices[0].message.content
    text_to_audio(response)

    
    recognized_text = recognize_speech()
    while not recognized_text:
        print("You said:", recognized_text)
        with open("conversation.txt", "r") as file:
            convo = file.read()
            file.close()
        with open("conversation.txt", "a") as file:
            file.write("\nPerson: " + recognized_text + "\nRobot: " + response)
            file.close()
    converse()

def check_for_person(start_time):
    cv2.namedWindow('Body detection', cv2.WINDOW_NORMAL)
    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
    while start_time + 7 > time.time():

        capture = device.update()

        ret_color, color_image = capture.get_color_image()

        if not ret_color:
            continue

        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        bodies = body_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in bodies:
            cv2.rectangle(color_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
            converse()
            print("Saw a person. Going to continue the conversion!\n")

        cv2.imshow('Body detection', color_image)

        if cv2.waitKey(1) == ord('q'):
            break


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
    cv2.namedWindow('Body detection', cv2.WINDOW_NORMAL)
    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
    while move_goal is not None and not move_goal.is_finished:
        if start_convo:
            converse()
        continue

def cancel_goal():
    
    global move_goal
    if move_goal is not None:
        print("move goal cancelled")
        move_goal.cancel()
        move_goal = None




other_robot_pos = [0, 0]

robot_x = 0
robot_y = 0
# Function to handle client connections
def handle_client(client_socket, client_address):
    global other_robot_pos
    print(f"Connection from {client_address}")
    
    # Receive data from the client
    data = client_socket.recv(1024)  # Adjust buffer size as needed
    # print("Received:", data.decode())

    other_robot_pos = json.loads(data.decode())

    # Check if the received data indicates the presence of a person
        # Take appropriate action when a person is detected
    
    # Send a message back to the client
    if math.sqrt(pow(robot_x - other_robot_pos[0], 2) + pow(robot_y - other_robot_pos[1], 2)) < 2:
        print("WITHIN RANGE")
        response_message = "conversation started"
        client_socket.sendall(response_message.encode())
        client_socket.close()
        cancel_goal_with_timeout()
    else:
    # Close the connection
        client_socket.close()
        print(f"Connection with {client_address} closed")

# Define host and port
HOST = '10.0.0.145'  # Use 0.0.0.0 to listen on all available interfaces
PORT = 23457      # Choose a port (e.g., 12345)

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

start_convo = False

def cancel_goal_with_timeout():
    global move_goal, start_convo
    if move_goal is not None:
        print("ESFHISEJFOISHOSRHIOGSGISIROGSRI")
        start_convo = True
        move_goal.cancel()
        move_goal = None
        


while True:
    if incomplete_action:
        incomplete_action = False
        go_to_pos(last_destination)
    keys_list = [key for key in positions.keys() if key != last_destination] # make sure this works TODO
    random_position = random.choice(keys_list) # could make it so it excludes last destination key
    if random_position != last_destination:
        last_destination = random_position
        go_to_pos(random_position)


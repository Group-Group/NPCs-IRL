import roslibpy
import roslibpy.actionlib
import cv2
import pykinect_azure as pykinect
import time
import speech_recognition as sr
import platform
import os
from gtts import gTTS
import google.generativeai as genai
import os

GOOGLE_API_KEY ='AIzaSyA8VpElujIxJy1RWLO13KAdd5zDLxtAsI0'

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-pro')


with open("conversation.txt", "w") as file:
    file.write("")
    file.close()

def recognize_speech():
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Define the microphone as the source
    with sr.Microphone() as source:
        print("Listening...")

        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)

        # Record audio input from the microphone
        audio = recognizer.listen(source)

        print("Processing...")

    # Perform speech recognition
    try:
        # Recognize speech using Google Speech Recognition
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand audio.")
        return None
    except sr.RequestError as e:
        print("Error occurred during request to Google Speech Recognition service:", str(e))
        return None

def text_to_audio(text, language='en'):
    # Create a gTTS object
    tts = gTTS(text=text, lang=language)

    # Save the audio to a file
    tts.save("output.mp3")


    # Determine the command based on the operating system
    if platform.system() == 'Windows':
        os.system("start output.mp3")
    elif platform.system() == 'Darwin':  # macOS
        os.system("afplay output.mp3")
    else:  # Linux
        os.system("mpg123 output.mp3")  # Install mpg321: sudo apt-get install mpg321



client = roslibpy.Ros(host="0.0.0.0", port=9090)
client.run()
print("IS ROS CONNECTED ", client.is_connected)

action_client = roslibpy.actionlib.ActionClient(
    client, "/move_base", "move_base_msgs/MoveBaseAction" )

positions = {
    "tv_screen": [-0.424, 6.777, 0.217, 1.0],
    "coffee_table": [-0.619, -0.202, 0.217, 1.0]
}

# target is (x, y, quat z, quat w)
def go_to_pos(target, reached_goal):
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
    pykinect.initialize_libraries(module_k4abt_path='/usr/lib/libk4abt.so', track_body=False)

    # Modify camera configuration
    device_config = pykinect.default_configuration
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P

    # Start device
    device = pykinect.start_device(config=device_config)

    # Load the body cascade classifier
    # body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

    cv2.namedWindow('Body detection', cv2.WINDOW_NORMAL)
    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
    while move_goal is not None and not move_goal.is_finished:

        capture = device.update()

        # Get the color image from the capture
        ret_color, color_image = capture.get_color_image()

        if not ret_color:
            continue

        # Convert color image to grayscale for body detection
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Detect bodies using cascade classifier
        bodies = body_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around the detected bodies
        for (x, y, w, h) in bodies:
            cv2.rectangle(color_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cancel_goal()
            start_convo()
            print("Person detected!\n")

        # Display the color image with body detection
        cv2.imshow('Body detection', color_image)



        # Press q key to stop
        if cv2.waitKey(1) == ord('q'):
            break

cv2.destroyAllWindows()

def cancel_goal():
    global move_goal
    if move_goal is not None:
        print("move goal cancelled")
        move_goal.cancel()
        move_goal = None

def destination_reached():
    print("I did it")

# You need to write code to block until the goal completes


def start_convo():
    recognized_text = recognize_speech()
    if recognized_text:
        print("You said:", recognized_text)
        with open("conversation.txt", "r") as file:
            convo = file.read()
            file.close()
        if convo == "":
            response = model.generate_content("You are a BWI robot, circiling the robotics lab and ran into a person and they started talking to you. They said \"" + recognized_text + "\". Respond to them with a casual greeting and reply to them if needed. Only write your response.")
        else:
            response = model.generate_content("You are a BWI robot, currently in a casual conversation with a person. The conversation so far has been \"" + convo + "\". They just said \"" + recognized_text + "\". Respond to them with a casual conversational response. Only write your response.")
        
        with open("conversation.txt", "a") as file:
            file.write("\nPerson: " + recognized_text + "\nRobot: " + response.text)
            file.close()
        text_to_audio(response.text)



go_to_pos("tv_screen", destination_reached) #example usage

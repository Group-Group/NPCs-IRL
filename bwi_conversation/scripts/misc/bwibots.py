from openai import OpenAI
import speech_recognition as sr
import roslibpy.actionlib
import roslibpy
import threads
import bwi_vision
from pathlib import Path
import platform
import os

""" some constants """

AIc = OpenAI(
    api_key="sk-proj-98CEKi821xDabqz4Lmi1T3BlbkFJWLZVBqJ15e7eqBxCwZCR"
)
landmarks = {
    "tv_screen": [-0.424, 6.777, 0.217, 1.0],
    "coffee_table": [-0.619, -0.202, 0.217, 1.0]
}

"""
todo vision , camera
"""

class bwirobot:
    """
    `bwirobots` should be able to
    * recognize someone's speech
    * play text to audio (speak)
    * respond to a message
    * look for people
    * roam a building
    * send its position to a server

    not all `bwirobots` can
    * start servers
    * initiate conversations with other robots
    """
    def __init__(self, client):
        self.action_client = roslibpy.actionlib.ActionClient(client, "/move_base", "move_base_msgs/MoveBaseAction")
        self.active_goal = None # the current move goal
        self.last_destination = None # string key for the landmarks dictionary
        self.completed_last_action = True
        self.chat = [] # list of strings
        self.vision = bwi_vision.bwivision()

    @staticmethod
    def recognize_speech():
        recognizer = sr.Recognizer()

        with sr.Microphone as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
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

    @staticmethod
    def speak(text):
        """text to speech"""
        speech_file_path = Path(__file__).parent / "output.mp3"
        response = AIc.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text
        )

        response.stream_to_file(speech_file_path)

        system = platform.system()
        if system == "Windows":
            os.system("start output.mp3")
        elif system == "Darwin": # mac
            os.system("afplay output.mp3")
        else: # Linux, dependency on mpg123
            os.system("mpg123 output.mp3")

    #todo
    def respond():
        pass

    def move_to(self, target):
        print("going to " + str(target))
        message = {
            "target_pose": {
                "header": {"frame_id": "level_mux_map"},
                "pose": {
                    "position": {"x": landmarks[target][0], "y": landmarks[target][1], "z": 0.0},
                    "orientation": {"x": 0.0, "y": 0.0, "z": landmarks[target][2], "w": landmarks[target][3]},
                },
            }
        }

        move_goal = roslibpy.actionlib.Goal(self.action_client, message)
        move_goal.send()

        self.active_goal = move_goal
        self.last_destination = target
        
        """
        todo need to decide how to handle the looking for people part
        todo do i want this in here or should it be a different method
        """

    def cancel_goal(self):
        if self.active_goal:
            print("cancelling goal")
            self.active_goal.cancel()
            self.active_goal = None
            self.completed_last_action = False

class clientbot(bwirobot):
    """
    `clientbots` have the same functions as `bwirobots` but they should
    * send their position to a server
    """
    def __init__(self):
        client = roslibpy.Ros(host="0.0.0.0", port=9090)
        client.run()
        super().__init__(client)
        self.th = threads.ClientThreadHandle(client)

    def prompted_for_conversation(self):
        return self.th.last_response_from_server == "conversation started"

class serverbot(bwirobot):
    """
    `serverbots` have the same functions as `bwirobots` but they can
    * start servers
    * check if they are close to another robot
    * initiate conversation with other robots
    
    """
    def __init__(self):
        client = roslibpy.Ros(host="0.0.0.0", port=9090)
        client.run()
        super().__init__(client)
        self.th = threads.ServerThreadHandle(client)

    def prompts_conversation(self):
        return self.th.last_message_sent == "conversation started"
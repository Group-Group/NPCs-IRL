from openai import OpenAI
import speech_recognition as sr
from playsound import playsound
import roslibpy.actionlib
import roslibpy
from pathlib import Path

from .threads import PORT, Client, Server, ClientThread, ServerThread
from .bwi_vision import bwivision
from .chatsession import ChatSession


""" some constants """

AIc = OpenAI(
    api_key="sk-proj-BoQ0NfI5mra6q02ts07lT3BlbkFJ0E081wZQFK35rXTo1X0g"
)
landmarks = {
    "tv_screen": [-0.424, 6.777, 0.217, 1.0],
    "coffee_table": [-0.619, -0.202, 0.217, 1.0]
}

class bwirobot:
    """
    `bwirobots` should be able to
    * recognize someone's speech
    * play text to audio (speak)
    * respond to a message
    * look for people
    * roam a building

    not all `bwirobots` can
    * start servers
    * initiate conversations with other robots
    * send its position to a server
    """
    def __init__(self, client, enable_vision):
        self.action_client = roslibpy.actionlib.ActionClient(client, "/move_base", "move_base_msgs/MoveBaseAction")
        self.active_goal = None # the current move goal
        self.last_destination = None # string key for the landmarks dictionary
        self.completed_last_action = True
        self.chat = None

        self.vision = None
        if enable_vision:
            self.vision = bwivision()

    def ask_chat(self, prompt):
        self.chat.log_prompt(prompt)

        generated_response = AIc.chat.completions.create(
                messages=self.chat.history,
                model="gpt-3.5-turbo"
        )

        text = generated_response.choices[0].message.content
        raw = generated_response.choices[0].message

        return text, raw

    def recognize_speech(self):
        recognizer = sr.Recognizer()

        # make 2 attempts to recognize speech
        attempts = 0

        while attempts < 2:
            attempts += 1
            with sr.Microphone() as source:
                print("Say something...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            try:
                speech = recognizer.recognize_google(audio)
                print("You said: " + speech)
                return speech
            except sr.UnknownValueError:
                print("Sorry, I could not understand what you said.")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

        self.chat.is_ongoing = False
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
        playsound(speech_file_path)
        
    def start_person_conversation(self):
        print('starting person conversation' + "\n" * 50)

        chat = ChatSession(has_person=True)
        self.chat = chat

        other_response = self.recognize_speech()
        if other_response is None or not ("hello" in other_response or "hi" in other_response or "hey" in other_response):
            chat.is_ongoing = False
            return chat
        
        response, raw = self.ask_chat(f"You are a BWI robot and a person said *{other_response}* to you. Introduce yourself and write an appropriate response to them.")
        self.speak(response)
        chat.send_message(raw)

        return chat
    
    def respond(self):
        print("waiting for a response")

        if self.chat.has_person: # need to detect speech
            other_response = self.recognize_speech()
            self.chat.is_ongoing = other_response is not None

            if self.vision: # make sure the person is engaged
                self.chat.is_ongoing = self.chat.is_ongoing and self.vision.person_detected

        else: # wait for a message over the socket
            other_response = self.chat.wait_for_message()
            self.chat.is_ongoing = "Goodbye" not in other_response and len(self.chat.history) <= 5 # (self.chat.history and len(self.chat.history) > 5)
        print(f"received response: {other_response}")

        # chat state might have changed from above, give an appropriate response
        if self.chat.is_ongoing:
            response, raw = self.ask_chat(f"They said {other_response}. Write an appropriate response to them.")
        else:
            response, raw = self.ask_chat(f"Say goodbye! Be very brief but cordial. Say only a few words.")
        
        self.speak(response)
        self.chat.send_message(raw)

        return self.chat

    def move_to(self, target):
        print("going to " + str(target))

        if type(target) == str: # target is in the landmarks dict
            self.last_destination = target
            target = landmarks[target]

        message = {
            "target_pose": {
                "header": {"frame_id": "level_mux_map"},
                "pose": {
                    "position": {"x": target[0], "y": target[1], "z": 0.0},
                    "orientation": {"x": 0.0, "y": 0.0, "z": target[2], "w": target[3]},
                },
            }
        }

        move_goal = roslibpy.actionlib.Goal(self.action_client, message)
        move_goal.send()

        self.active_goal = move_goal

    def cancel_goal(self):
        if self.active_goal:
            self.active_goal.cancel()
            self.active_goal = None
            self.completed_last_action = False

class clientbot(bwirobot):
    """
    `clientbots` have the same functions as `bwirobots` but they should
    * send their position to a server
    * connect to a conversation server
    """
    def __init__(self, enable_vision=True):
        client = roslibpy.Ros(host="0.0.0.0", port=9090)
        client.run()
        super().__init__(client, enable_vision)
        self.chat_client = None # client, when we need to join a conversation server

        # to send our position to the server
        self.thread = ClientThread(client)

    def prompted_for_conversation(self):
        return self.thread.last_response_from_server == "conversation started"

    def join_conversation_server(self):
        chat_client = Client()
        chat_client.connect_to_server(port=PORT + 1000)
        self.chat_client = chat_client

        chat = ChatSession(chat_client.client_socket)
        chat.log_prompt("You are currently in a conversation with another BWI robot. Write an appropriate response to them with your personality.")
        self.chat = chat
        return chat
        
    def leave_conversation(self):
        self.chat = None
        self.thread.last_response_from_server = None

        if self.chat_client:
            self.chat_client.close_connection_to_server()
            self.chat_client = None

class serverbot(bwirobot):
    """
    `serverbots` have the same functions as `bwirobots` but they can
    * start location servers
    * start conversation servers
    * check if they are close to another robot
    * initiate conversation with other robots
    
    """
    def __init__(self, enable_vision=True):
        client = roslibpy.Ros(host="0.0.0.0", port=9090)
        client.run()
        super().__init__(client, enable_vision)

        # start a conversation server
        chat_server = Server()
        chat_server.start_server(port=PORT + 1000)
        self.chat_server = chat_server

        # start a ROS location server
        self.thread = ServerThread(client)

    def prompts_conversation(self):
        return self.thread.last_message_sent == "conversation started"
    
    def start_robot_conversation(self):
        # wait for client to connect
        client_socket, client_addr = self.chat_server.server_socket.accept()
        print(f"client connected at {client_addr}.")

        chat = ChatSession(client_socket)
        self.chat = chat
        
        response, raw = self.ask_chat("Talk about whatever you want. ** Be brief in your response.")
        self.speak(response)

        chat.send_message(raw)
        return chat
from openai import OpenAI
import speech_recognition as sr
from playsound import playsound
import roslibpy.actionlib
import roslibpy
from pathlib import Path

from .threads import PORT, ClientHandle, ServerHandle, ClientThreadHandle, ServerThreadHandle
# from .bwi_vision import bwivision
from .chatsession import ChatSession


""" some constants """

AIc = OpenAI(
    api_key="sk-proj-98CEKi821xDabqz4Lmi1T3BlbkFJWLZVBqJ15e7eqBxCwZCR"
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
    def __init__(self, client):
        self.action_client = roslibpy.actionlib.ActionClient(client, "/move_base", "move_base_msgs/MoveBaseAction")
        self.active_goal = None # the current move goal
        self.last_destination = None # string key for the landmarks dictionary
        self.completed_last_action = True
        self.chat = None # []
        # self.vision = bwivision()

    def ask_chat(self, prompt):
        self.chat.log_prompt(prompt)

        generated_response = AIc.chat.completions.create(
                messages=self.chat.history,
                model="gpt-3.5-turbo"
        )

        text = generated_response.choices[0].message.content
        raw = generated_response.choices[0].message

        return text, raw

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
            voice="nova",
            input=text
        )

        response.stream_to_file(speech_file_path)
        playsound(speech_file_path)
        
    def respond(self):
        """ need logic for people / robot convo """
        print("waiting for a response")
        other_response = self.chat.wait_for_message()

        print(f"received response: {other_response}")
        response, raw = self.ask_chat(f"They said {other_response}. Write an appropriate response to them.")

        self.speak(response)

        self.chat.send_message(raw)
        return self.chat

        # client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client_socket.connect((HOST, PORT + 1000))
        # print("Connected to server successfully!")

        # print("waiting for response")
        # while True:
        #     response = client_socket.recv(1024).decode()
        #     print("Received from server: ", response)
        #     self.chat.append(response)

        #     generated_response = AIc.chat.completions.create(
        #         messages=[
        #             {
        #                 "role": "user",
        #                 "content": "You are submissive robot and you are currently in a conversation with an alpha male robot. They said " + response + " write an appropriate response to them with your personality."
        #             },
        #         ],
        #         model="gpt-3.5-turbo"
        #     )

        #     this_response = generated_response.choices[0].message.content
        #     self.chat.append(this_response)
        #     self.speak(this_response)
        #     # audio = AudioSegment.from_file("output.mp3")
        #     # length_ms = len(audio)
        #     # length_seconds = length_ms / 1000
        #     print("sending my response")
        #     client_socket.sendall(this_response.encode())

        #     # Close socket
        # client_socket.close()

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
    * connect to a conversation server
    """
    def __init__(self):
        client = roslibpy.Ros(host="0.0.0.0", port=9090)
        client.run()
        super().__init__(client)
        self.ch = None # client handle
        self.th = ClientThreadHandle(client)

    def prompted_for_conversation(self):
        return self.th.last_response_from_server == "conversation started"

    def join_conversation_server(self):
        ch = ClientHandle()
        ch.connect_to_server(port=PORT + 1000)
        self.ch = ch

        chat = ChatSession(ch.client_socket)
        chat.log_prompt("You are submissive robot and you are currently in a conversation with an alpha male robot. Write an appropriate response to them with your personality.")
        self.chat = chat
        return chat
        
    def leave_conversation_server(self):
        self.chat = None
        self.ch.close_connection_to_server()
        self.ch = None

class serverbot(bwirobot):
    """
    `serverbots` have the same functions as `bwirobots` but they can
    * start location servers
    * start conversation servers
    * check if they are close to another robot
    * initiate conversation with other robots
    
    """
    def __init__(self):
        client = roslibpy.Ros(host="0.0.0.0", port=9090)
        client.run()
        super().__init__(client)
        sh = ServerHandle()
        sh.start_server(port=PORT + 1000)
        self.sh = sh
        self.th = ServerThreadHandle(client)

    def prompts_conversation(self):
        return self.th.last_message_sent == "conversation started"
    
    def start_conversation(self):
        print('starting the conversation' + "\n" * 50)

        # wait for client to connect
        client_socket, client_addr = self.sh.server_socket.accept()
        print(f"client connected at {client_addr}.")

        chat = ChatSession(client_socket)
        self.chat = chat
        response, raw = self.ask_chat("You are a BWI robot that is an absolute giga chad circling the robotics lab and you ran into a submissive robot. Introduce yourself and ask them about their plans. Write only what you would say.")
        self.speak(response)

        chat.send_message(raw)
        return chat
        

import json
import random

class ChatSession:
    """
    `chatsession` handles sending and receiving messages and keeps track of the chat history.
    ### Methods
    * `log_prompt`: record a message in chat history as the user giving prompts to chatgpt
    * `wait_for_message`: wait for and return the message sent by the client / server
    * `send_message`: send the raw message generated by chatgpt

    ### Attributes
    * `conversation_socket`: the socket used to send and receive messages
    """
    def __init__(self, conversation_socket=None, has_person=False):
        self.max_messages = 4 # random.randint(1, 909124)
        self.conversation_socket = conversation_socket
        self.history = [] # must be a list of properly formatted messages
        self.is_ongoing = True
        self.has_person = has_person

    def log_prompt(self, prompt):
        """ log user prompts """
        # format properly
        logged = {
            'role': 'user',
            'content': prompt
        }
        self.history.append(logged)
    
    def wait_for_message(self):
        response = self.conversation_socket.recv(1024).decode()
        print("Received response")
        # break down into text
        response = json.loads(response)
        self.history.append(response)
        return response["content"]

    def send_message(self, message, force_stop):
        """ log a formatted message in chat history and send it to the server / client """
        
        print("\n" * 50)
        # format message as dictionary
        formatted = {
            'role': 'assistant',
            'content': message.content,
        }
        
        self.is_ongoing = len(self.history) / 2 < self.max_messages and not force_stop
        self.history.append(formatted)

        if force_stop and not self.has_person:
            formatted = {
                'role': 'assistant',
                'content': "Goodbye",
            }
            formatted = json.dumps(formatted)
            self.conversation_socket.sendall(formatted.encode())
        elif self.conversation_socket and not self.has_person:
            formatted = json.dumps(formatted)
            self.conversation_socket.sendall(formatted.encode())

        print("Sent message ", formatted)
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
        # break down into text
        response = json.loads(response)
        self.history.append(response)
        return response["content"]

    def send_message(self, message):
        """ log a formatted message in chat history and send it to the server / client """
        
        formatted = {
            'role': 'assistant',
            'content': message.content,
        }
        
        self.history.append(formatted)

        if self.conversation_socket is not None:
            if not self.is_ongoing:
                formatted = {
                    'role': 'user',
                    'content': 'Goodbye',
                }

            formatted = json.dumps(formatted)
            self.conversation_socket.sendall(formatted.encode())

        print("Sent message ", formatted)

    def save_to_file(self, path="conversation.txt"):
        with open(path, "w") as file:
            for i, message in enumerate(self.history):
                speaker = 'user' if i % 3 == 0 else 'bender' if i % 3 == 1 else 'nova'
                file.write(f"{speaker}: {message['content']}\n")
                print(f"{speaker}: {message['content']}")

        print("Conversation written to ", path)

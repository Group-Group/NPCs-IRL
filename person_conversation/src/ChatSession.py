import google.ai.generativelanguage as glm
from random import randint
import typing

type ChatState = typing.Literal["ongoing", "ending", "finished"]

class ChatSession:
    def __init__(self, id: str = "0", participants: list = [], ignore_system: bool = True, always_continue: bool = False):
        """Arguments:
        * id: this `ChatSession`'s id
        * participants: a list of `Talker` class robots
        * ignore_system: boolean to print system messages
        * always_continue: boolean to control chat session flow
        """
        self.id: str = id
        self.messages: list[glm.Content] = []
        self.state: ChatState = "ongoing"
        self.participants: list = participants
        self.ignore_system: bool = ignore_system
        self.maximum_messages: int = randint(2, 4) if not always_continue else 0 # Maximum number of messages per robot
        self.always_continue = always_continue # Continue the conversation until the person leaves, False if there is no person

    def send_message(self, sender: str, message: glm.Content):
        """
        Log a message in the conversation history\n
        You should not call this method directly. This method is invoked through `Talker.respond`.
        """
        self.messages.append(message)
        print(f"\nRECEIVED MESSAGE FROM {sender}")
        print(message.parts[0].text)

    def send_system_message(self, message: glm.Content):
        """
        Log a message in the conversation history as the system\n
        You should not call this method directly.
        """
        self.messages.append(message)
        if not self.ignore_system:
            print(f"\nsystem message")
            print(message.parts[0].text)
    
    def update_state(self):
        """Update this conversation's `state`. This is done at the end of each conversation cycle."""
        if (self.state == "ongoing"):
            messages_per_robot = len(self.messages) / (2 * len(self.participants))
            self.state = "ongoing" if (self.always_continue or self.maximum_messages >= messages_per_robot) else "ending"
        elif (self.state == "ending"):
            self.state = "finished"

    def save(self, path = None):
        if path == None:
            path = f"conversation{self.id}.txt"

        with open(path, "w") as file:
            for message, i in enumerate(self.messages):
                file.write(i + ":\t" + message.sender)
                file.write("\t" + message.content)
            file.write("------------------ END OF CHAT ------------------")

        print(f"Conversation (id={self.id}) written to {path}.")

    @staticmethod
    def to_content(message: str) -> glm.Content:
        part = glm.Part(text=message)
        content = glm.Content(role='user')
        content.parts.append(part)
        return content
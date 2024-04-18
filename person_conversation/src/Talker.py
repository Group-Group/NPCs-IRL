import os
import google.generativeai as genai
import google.ai.generativelanguage as glm
from ChatSession import ChatSession

type GenerativeModel = genai.GenerativeModel
GOOGLE_API_KEY = 'AIzaSyA8VpElujIxJy1RWLO13KAdd5zDLxtAsI0' #** use os.getenv when public
genai.configure(api_key=GOOGLE_API_KEY)

class Talker:    
    def __init__(self, name: str):
        self.name: str = name
        self.model: GenerativeModel = genai.GenerativeModel('gemini-pro')

    def start_conversation(self, robots: list) -> ChatSession: #! need boolean if there is a guy
        """Start a new conversation, return the new `ChatSession`."""
        # Comma separated string of participants
        participants = ", ".join(member.name for member in robots)

        # Start a chat history
        robots.append(self)
        chat = ChatSession(participants=robots)
        INIT_PROMPT = f"You are a BWI robot named \"{self.name}\" circling the robotics building. Today you met with three people. \n\nCurrently, you are running into BWI robot(s) named \"{participants}\", start a casual conversation with them. Write only what you would say."
        chat.send_system_message(ChatSession.to_content(INIT_PROMPT))

        # Prompt the model for its response, append to chat history
        response = self.model.generate_content(chat.messages)
        chat.send_message(self.name, response.candidates[0].content)
        return chat
    
    def respond(self, chat: ChatSession) -> ChatSession:
        """Respond as a participant in an existing chat, return the `ChatSession`."""
        if chat.state == "ongoing":
            PROMPT = f"You are a BWI robot named \"{self.name}\" circling the robotics building. \n\nYou are currently in a conversation with other BWI robot(s). Continue the conversation but be brief and casual in your response. Do not repeat what the other participants or yourself have already said. Write only what {self.name} says."
        elif chat.state == "ending":
            PROMPT = f"You are a BWI robot named \"{self.name}\" circling the robotics building. \n\nWrap up your current conversation and say goodbye to the other robot(s) from {self.name}'s perspective. Do not repeat what the other participants or yourself have already said."
        
        if chat.state != "finished":
            chat.send_system_message(ChatSession.to_content(PROMPT))  
            response = self.model.generate_content(chat.messages)
            chat.send_message(self.name, response.candidates[0].content)
            return chat


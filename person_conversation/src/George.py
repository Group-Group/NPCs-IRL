from Talker import Talker

# Demo talker AI


George = Talker("George")
Jeff = Talker("Jeff")
Nigel = Talker("Nigel")
chat = George.start_conversation([Nigel, Jeff]) # fill this in with who george is talking to

while chat.state != "ending":
    Nigel.respond(chat)
    Jeff.respond(chat)
    George.respond(chat)
    chat.update_state()

# Say goodbye
while chat.state != "finished":
    Nigel.respond(chat)
    Jeff.respond(chat)
    George.respond(chat)
    chat.update_state()

# 1st AI
# import json
# import google.generativeai as genai
# import os
# import time

# GOOGLE_API_KEY ='AIzaSyA8VpElujIxJy1RWLO13KAdd5zDLxtAsI0'

# genai.configure(api_key=GOOGLE_API_KEY)


# # Start the conversation among two BWI robots
# model = genai.GenerativeModel('gemini-pro')

# response = model.generate_content("You are a BWI robot named \"George\" circling the robotics building. Today you met with three people. \n\nCurrently, you are running into another BWI robot named \"Nigal\", start a casual conversation with Nigal. Write only what you would say.")

# with open("conversation.txt", "w") as file:
#     file.write("George: " + response.text + " 0")
#     file.close()


# # Waiting until the robots have finished their conversation 
# # (signified by the last character in the file being "1" at the moment)
# def wait_until_written(file_path, timeout=60, poll_interval=1):
#     start_time = time.time()
#     while time.time() - start_time < timeout:
#         with open(file_path, "r") as file:
#             other_response = file.read()
#             file.close()
#         if other_response[-1] == "1":
#             return True
#         time.sleep(poll_interval)
#     return False


# # Continue the conversation until one of the robots says "Goodbye"
# while True:
#     if wait_until_written("conversation.txt") == True:
        
#         with open(f"conversation.txt", "r") as file:
#             other_response = file.read()
#             file.close()
#         if "Goodbye" not in other_response:
#             response = model.generate_content("You are a BWI robot named \"George\" circling the robotics building. \n\nCurrently, you are in a conversation with another BWI robot named \"Nigal\". Your casual conversation with Nigal so far is, \"" + other_response +  "\". Write a response to Nigal. Write only what you would say. Don't be hasty, keep the convesation casual, but if the conversation is over \"Goodbye\".")
#             with open(f"conversation.txt", "a") as file:
#                 file.write("\nGeorge: " + response.text + " 0")
#                 file.close()
#             if "Goodbye" in response.text:
#                 print("Conversation is over")
#                 break
#         else:
#             print("Conversation is over")
#             break
#     else: 
#         break

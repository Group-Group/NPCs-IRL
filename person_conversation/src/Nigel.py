# 2nd Ai
import google.generativeai as genai
import os
import time


GOOGLE_API_KEY ='AIzaSyA8VpElujIxJy1RWLO13KAdd5zDLxtAsI0'

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-pro')


# Read the start of the robots other conversation
with open(f"conversation.txt", "r") as file:
    other_response = file.read()
    file.close()

# Respond to the start of their conversation
response = model.generate_content("You are a BWI robot named \"Nigal\" circling the robotics building. Today you met with one person. \n\nCurrently, you are running into another BWI robot named \"George\". George said, \"" + other_response +  "\". Write a response to George. Write only what you would say.")

with open(f"conversation.txt", "a") as file:
    file.write("\nNigal: " + response.text + " 1")
    file.close()


# Waiting until the robots have finished their conversation 
# (signified by the last character in the file being "0" at the moment)
def wait_until_written(file_path, timeout=60, poll_interval=1):
    start_time = time.time()
    while time.time() - start_time < timeout:
        with open(file_path, "r") as file:
            other_response = file.read()
            file.close()
        if other_response[-1] == "0":
            return True
        time.sleep(poll_interval)
    return False


# Continue the conversation until one of the robots says "Goodbye"
while True:
    if wait_until_written(f"conversation.txt") == True:
        with open(f"conversation.txt", "r") as file:
            other_response = file.read()
            file.close()
        if "Goodbye" not in other_response:
            response = model.generate_content("You are a BWI robot named \"Nigal\" circling the robotics building. Today you met with three people. \n\nCurrently, you are in a casual conversation another BWI robot named \"George\". Your casual conversation with George so far is, \"" + other_response +  "\". Write a response to George. Write only what you would say. Don't be hasty, keep the convesation casual, but if the conversation is over, write \"Goodbye\".")
            with open(f"conversation.txt", "a") as file:
                file.write("\nNigal: " + response.text + " 1")
                file.close()
            if "Goodbye" in response.text:
                print("Conversation is over")
                break
        else:
            print("Conversation is over")
            break
    else: 
        break
import random
from npc_lib import bwibots

nova = bwibots.clientbot()

"""
todo need to test:
-- threads.py: connect to server in init
-- chatsession class
-- clienthandle, serverhandle class
-- if i need to connect to server in a while true loop and close sockets after sending a message

todo cooldown after talking to robot
todo figure out if i need to kill sockets / threads when shutting down
"""

while True:
    try:
        if not nova.completed_last_action:
            nova.completed_last_action = True
            nova.move_to(nova.last_destination)
        else:
            next_destination = random.choice(list(bwibots.landmarks.keys()))
            if next_destination == nova.last_destination:
                continue

            nova.last_destination = next_destination
            nova.move_to(next_destination)

        while nova.active_goal is not None and not nova.active_goal.is_finished:
            # nova.vision.check_for_person()
            flagged_for_conversation = nova.prompted_for_conversation() # nova.vision.detects_person()

            if (flagged_for_conversation):
                nova.cancel_goal()
                chat = nova.join_conversation_server()
                
                while chat.is_ongoing:
                    nova.respond()
                
                nova.leave_conversation_server()

    except:
        nova.cancel_goal()
        # nova.vision.close()
        break

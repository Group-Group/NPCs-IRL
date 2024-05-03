import random
from npc_lib import bwibots

"""
todo need to test:
-- threads.py: connect to server in init

todo cooldown after talking to robot
todo integrate robot / person convo
todo check robot runs w/o client or server (use bwibot class)
todo nltk

todo figure out if i need to kill sockets / threads when shutting down

todo if time, multiparty and mixed conversations
"""

nova = bwibots.clientbot()

try:
    while True:
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
            flagged_for_conversation = nova.prompted_for_conversation() # or nova.vision.detects_person()

            if (flagged_for_conversation):
                nova.cancel_goal()
                chat = nova.join_conversation_server()
                
                while chat.is_ongoing:
                    nova.respond()
                
                nova.leave_conversation_server()

except Exception as e:
    print(e)
    nova.cancel_goal()
    # nova.vision.close()

import random
from npc_lib import bwibots

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
            person_detected = nova.vision and nova.vision.person_detected
            if person_detected:
                nova.thread.send_far = True
            
            flagged_for_conversation = nova.prompted_for_conversation() or person_detected

            if (flagged_for_conversation):
                nova.cancel_goal()

                if person_detected:
                    chat = nova.start_person_conversation()
                    while chat and chat.is_ongoing:
                        nova.respond()

                else: 
                    chat = nova.join_conversation_server()
                    while chat and chat.is_ongoing:
                        nova.respond()
                
                while chat.is_ongoing:
                    nova.respond()
                    
                print("conversation over")
                nova.leave_conversation()

                nova.thread.send_far = False

except Exception as e:
    print(e)
    nova.cancel_goal()
    # nova.vision.close()

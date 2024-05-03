import random
from npc_lib import bwibots

"""
face detection vs robot detection
-- prioritize faces

chat collisions
-- one robot talking to a person

cooldowns

"""

bender = bwibots.serverbot()

try:
    while True:
        if not bender.completed_last_action:
            bender.completed_last_action = True
            bender.move_to(bender.last_destination)
        else:
            next_destination = random.choice(list(bwibots.landmarks.keys()))
            if next_destination == bender.last_destination:
                continue # try again

            bender.last_destination = next_destination
            bender.move_to(next_destination)

        # this is a blocking loop
        while bender.active_goal is not None and not bender.active_goal.is_finished:
            bender.vision.check_for_person()
            person_detected = bender.vision.detects_person()
            flagged_for_conversation = bender.prompts_conversation() or person_detected

            if (flagged_for_conversation):
                bender.cancel_goal()

                if person_detected:
                    chat = bender.start_person_conversation()
                else:
                    bender.move_to(bender.thread.last_location_seen)
                    chat = bender.start_robot_conversation()
                
                while chat.is_ongoing:
                    bender.respond()

                bender.chat = None

except Exception as e:
    print(e)
    bender.cancel_goal()
    # bender.vision.close()

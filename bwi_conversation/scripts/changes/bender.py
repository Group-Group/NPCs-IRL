import random
from npc_lib import bwibots

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
            # bender.vision.check_for_person()
            flagged_for_conversation = bender.prompts_conversation() # or bender.vision.detects_person()

            if (flagged_for_conversation):
                bender.cancel_goal()
                bender.move_to(bender.thread.last_location_seen)
                chat = bender.start_conversation()
                
                while chat.is_ongoing:
                    bender.respond()

                bender.chat = None

except Exception as e:
    print(e)
    bender.cancel_goal()
    # bender.vision.close()

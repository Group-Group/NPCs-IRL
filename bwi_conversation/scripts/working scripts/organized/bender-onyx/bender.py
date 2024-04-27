import random
import bwibots

bender = bwibots.serverbot()
bender.move_to('tv_screen')
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
        flagged_for_conversation = bender.prompts_conversation() # or bender.vision.detects_person()

        if (flagged_for_conversation):
            bender.cancel_goal()
            
            while True:
                bender.start_conversation()
            
        # """
        # if (need to start conversation):
        #     bender.cancel_goal()
        #     bender.start_conversation()
            
        #     then do all the conversation generating here, send it to client
        #     -- no need for a stop word, just generate a random num of messages
        #     -- if there are no messages left, tell them to say goodbye and continue on

        #     if talking to a person
        #     -- recognize speech
        #     -- get response
        #     -- speak
        # """

import random
import bwibots

nova = bwibots.clientbot()
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
        nova.vision.check_for_person()
        flagged_for_conversation = nova.vision.detects_person()
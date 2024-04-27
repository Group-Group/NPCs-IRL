#!/usr/bin/env python

import rospy
import actionlib
from actionlib_msgs.msg import GoalID
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import time
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np

face_detected = False
positions = {
    "tv_screen": [-0.424, 6.777, 0.217],
    "coffee_table": [-0.619, -0.202, 0.217]
}

def image_callback(msg):
    global face_detected
    bridge = CvBridge()
    cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    # Load the pre-trained face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    if len(faces) > 0:
        face_detected = True

def movebase_client():
    global face_detected

    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    client.wait_for_server()

    positions = [[-0.424, 6.777, 0.217],
                 [-0.619, -0.202, 0.217]]

    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "level_mux_map"
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = positions["tv_screen"][0]
    goal.target_pose.pose.position.y = positions["tv_screen"][1]
    goal.target_pose.pose.position.z = positions["tv_screen"][2]
    goal.target_pose.pose.orientation.w = 1.0

    start = time.time()
    client.send_goal(goal)
    wait = client.wait_for_result()

    cap = cv2.VideoCapture(1)

    while True:
        ret, frame = cap.read()
        cv2.imshow('Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    rospy.loginfo("Move finished")
    if not wait:
        rospy.logerr("Action server not available!")
        rospy.signal_shutdown("Action server not available!")
    else:
        return client.get_result()

if __name__ == '__main__':
    try:
        rospy.init_node('movebase_client_py')

        # Subscribe to the image topic to detect faces
        image_sub = rospy.Subscriber("/camera/image_raw", Image, image_callback)

        result = movebase_client()

        if result:
            rospy.loginfo("Goal execution done! Moved 1 forward")

        # If a face is detected, cancel the goal
        if face_detected:
            client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
            client.cancel_goal()
            rospy.loginfo("Goal cancelled due to face detection")

    except rospy.ROSInterruptException:
        rospy.loginfo("Navigation test finished.")


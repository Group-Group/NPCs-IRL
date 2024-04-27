#!/usr/bin/env python

import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import pykinect_azure as pykinect

class BodyDetectionNode:
    def __init__(self):
        rospy.init_node('body_detection_node')

        # Initialize the library
        pykinect.initialize_libraries(module_k4abt_path='/usr/lib/libk4abt.so', track_body=False)

        # Modify camera configuration
        self.device_config = pykinect.default_configuration
        self.device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P

        # Start device
        self.device = pykinect.start_device(config=self.device_config)

        # Load the body cascade classifier
        self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

        # Initialize ROS publisher for the detected body image
        self.image_pub = rospy.Publisher('/body_detection/image', Image, queue_size=10)

        # Initialize CvBridge
        self.cv_bridge = CvBridge()

    def detect_bodies(self):
        # Get capture
        capture = self.device.update()

        # Get the color image from the capture
        ret_color, color_image = capture.get_color_image()

        if not ret_color:
            return

        # Convert color image to grayscale for body detection
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Detect bodies using cascade classifier
        bodies = self.body_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around the detected bodies
        for (x, y, w, h) in bodies:
            cv2.rectangle(color_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
            rospy.loginfo("Person detected!")

        # Convert the image to ROS format
        image_msg = self.cv_bridge.cv2_to_imgmsg(color_image, encoding="bgr8")

        # Publish the image
        self.image_pub.publish(image_msg)

    def run(self):
        rate = rospy.Rate(10)  # 10 Hz
        while not rospy.is_shutdown():
            self.detect_bodies()
            rate.sleep()

if __name__ == "__main__":
    try:
        body_detection_node = BodyDetectionNode()
        body_detection_node.run()
    except rospy.ROSInterruptException:
        pass

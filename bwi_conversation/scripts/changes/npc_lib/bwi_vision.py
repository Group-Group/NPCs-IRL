import cv2
import pykinect_azure as pykinect
import time
from mtcnn import MTCNN # pip install mtcnn and pip install tensorflow-gpu

pykinect.initialize_libraries(module_k4abt_path='/usr/lib/libk4abt.so', track_body=False)

device_config = pykinect.default_configuration
device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P
device = pykinect.start_device(config=device_config)

TIMEOUT_SECS = 7

MINIMUM_WIDTH = 125
MINIMUM_HEIGHT = 125
class bwivision:
    """
    `bwivision` handles the person detection.
    ### Methods
    * detects_person: checks if there was a person seen in the last 7 seconds
    * check_for_person: checks if there is a person in the current frame
    """
    def __init__(self):
        self.last_detection_time = -float('inf')
        self.person_detected = False
        # self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
        # self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.detector = MTCNN()
        # create a new window
        cv2.namedWindow("Body detection", cv2.WINDOW_NORMAL)

        # new method
        

    @staticmethod
    def close():
        cv2.destroyAllWindows()

    def detects_person(self):
        self.person_detected = time.time() - self.last_detection_time < TIMEOUT_SECS
        return self.person_detected

    def check_for_person(self):        
        capture = device.update()
        ret_color, color_image = capture.get_color_image()
        if not ret_color:
            return

        faces = self.detector.detect_faces(color_image)
        
        # Draw rectangles around the detected faces
        for face in faces:
            x, y, width, height = face['box']
            if width > MINIMUM_WIDTH and height > MINIMUM_HEIGHT:
                cv2.rectangle(color_image, (x, y), (x+width, y+height), (0, 255, 0), 2)
                self.last_detection_time = time.time()
                self.person_detected = True
        
        
        # gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        # bodies = self.cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        # for (x, y, w, h) in bodies:
        #     if w > MINIMUM_WIDTH and h > MINIMUM_HEIGHT:
        #         cv2.rectangle(color_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
        #         print("Saw a person. Going to continue the conversion!\n")
        #         self.last_detection_time = time.time()
        #         self.person_detected = True

        cv2.imshow('Body detection', color_image)
        cv2.waitKey(1)

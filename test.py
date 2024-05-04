from mtcnn import MTCNN
import cv2

def detect_faces_camera():
    # Initialize the MTCNN detector
    detector = MTCNN()
    
    # Open the default camera (usually the webcam)
    cap = cv2.VideoCapture(1)
    
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        # Detect faces in the frame
        faces = detector.detect_faces(frame)
        
        # Draw rectangles around the detected faces
        for face in faces:
            x, y, width, height = face['box']
            cv2.rectangle(frame, (x, y), (x+width, y+height), (0, 255, 0), 2)
        
        # Display the result
        cv2.imshow('Face Detection', frame)
        
        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the camera and close the window
    cap.release()
    cv2.destroyAllWindows()

# Call the function to start face detection from the camera
detect_faces_camera()

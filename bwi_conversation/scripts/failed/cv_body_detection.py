
import cv2
import pykinect_azure as pykinect

if __name__ == "__main__":
    # Initialize the library, if the library is not found, add the library path as argument
    pykinect.initialize_libraries(module_k4abt_path='/usr/lib/libk4abt.so', track_body=False)

    # Modify camera configuration
    device_config = pykinect.default_configuration
    device_config.color_resolution = pykinect.K4A_COLOR_RESOLUTION_1080P

    # Start device
    device = pykinect.start_device(config=device_config)

    # Load the body cascade classifier
    # body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

    cv2.namedWindow('Body detection', cv2.WINDOW_NORMAL)
    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

    while True:
        # Get capture
        capture = device.update()

        # Get the color image from the capture
        ret_color, color_image = capture.get_color_image()

        if not ret_color:
            continue

        # Convert color image to grayscale for body detection
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Detect bodies using cascade classifier
        bodies = body_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Draw rectangles around the detected bodies
        for (x, y, w, h) in bodies:
            cv2.rectangle(color_image, (x, y), (x+w, y+h), (255, 0, 0), 2)
            face_detected = True
            print("Person detected!\n")

        # Display the color image with body detection
        cv2.imshow('Body detection', color_image)



        # Press q key to stop
        if cv2.waitKey(1) == ord('q'):
            break

cv2.destroyAllWindows()


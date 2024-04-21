# By Aryan and Noor and Quan and Vincent
import cv2
import time
import speech_recognition as sr
import platform
import os
from gtts import gTTS
import google.generativeai as genai
import os
import speech_recognition as sr
import time

my_number = 1

GOOGLE_API_KEY ='AIzaSyA8VpElujIxJy1RWLO13KAdd5zDLxtAsI0'

genai.configure(api_key=GOOGLE_API_KEY)

# model = genai.`GenerativeModel``('gemini-pro')


with open("conversation.txt", "w") as file:
    file.write("")
    file.close()

def recognize_speech():
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Define the microphone as the source
    with sr.Microphone() as source:
        print("Listening...")

        # Adjust for ambient noise
        recognizer.adjust_for_ambient_noise(source)

        # Record audio input from the microphone
        audio = recognizer.listen(source)

        print("Processing...")

    # Perform speech recognition
    try:
        # Recognize speech using Google Speech Recognition
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("Sorry, could not understand audio.")
        return None
    except sr.RequestError as e:
        print("Error occurred during request to Google Speech Recognition service:", str(e))
        return None



# Load the pre-trained face detection cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize video capture from the camera
cap = cv2.VideoCapture(1)  # Change the argument to the camera index if you have multiple cameras

# Initialize the recognizer
recognizer = sr.Recognizer()

def text_to_audio(text, language='en'):
    # Create a gTTS object
    tts = gTTS(text=text, lang=language)

    # Save the audio to a file
    tts.save("output.mp3")


    # Determine the command based on the operating system
    if platform.system() == 'Windows':
        os.system("start output.mp3")
    elif platform.system() == 'Darwin':  # macOS
        os.system("afplay output.mp3")
    else:  # Linux
        os.system("mpg321 output.mp3")  # Install mpg321: sudo apt-get install mpg321


# Variables to track if a person is detected and time since last detection
person_detected = False
last_detection_time = None
time_threshold = 5  # Adjust this threshold according to your needs (in seconds)

while True:
    # Read frame from the camera
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the grayscale frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    # Check if any faces are detected
    if len(faces) > 0:
        # Define the microphone as the source
        recognized_text = recognize_speech()
        if recognized_text:
            print("You said:", recognized_text)
            with open("conversation.txt", "r") as file:
                convo = file.read()
                file.close()
            if convo == "":
                response = genai.generate_content("You are a BWI robot, circiling the robotics lab and ran into a person and they started talking to you. They said \"" + recognized_text + "\". Respond to them with a casual greeting and reply to them if needed. Only write your response.")
            else:
                response = genai.generate_content("You are a BWI robot, currently in a casual conversation with a person. The conversation so far has been \"" + convo + "\". They just said \"" + recognized_text + "\". Respond to them with a casual conversational response. Only write your response.")
            
            with open("conversation.txt", "a") as file:
                file.write("\nPerson: " + recognized_text + "\nRobot: " + response.text)
                file.close()
            text_to_audio(response.text)
        # audio plays for potential response
        # Example usage
        


        person_detected = True
        last_detection_time = time.time()  # Update the last detection time

    else:
        # Check if enough time has passed since the last detection
        if last_detection_time is not None and time.time() - last_detection_time > time_threshold:
            person_detected = False
            
    if not person_detected:
        # reset the conversation and look for more people
        with open("conversation.txt", "w") as file:
            file.write("")
            file.close()


    # Draw rectangles around the detected faces
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Show the frame with detected faces
    cv2.imshow("Face Detection", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture and close OpenCV windows
cap.release()
cv2.destroyAllWindows()

# Check if a person (face) is currently detected and in frame
if person_detected:
    print("A person is in frame.")
else:
    print("No person is in frame.")

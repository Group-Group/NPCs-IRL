import socket
import cv2
import pickle
import struct
import numpy as np
import pyk4a as k4a

HOST = '0.0.0.0'  # Standard loopback interface address (localhost)
PORT = 9090        # Port to listen on (non-privileged ports are > 1023)

def send_kinect_feed():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server is listening on {HOST}:{PORT}")

        conn, addr = server_socket.accept()
        with conn:
            print(f"Connection from {addr}")

            # Initialize the Azure Kinect device
            k4a_device = k4a.Device.open()

            # Start camera capture
            k4a_device.start_cameras()

            while True:
                # Capture a frame from the Azure Kinect camera
                capture = k4a_device.get_capture(-1)
                depth_frame = capture.depth

                # Convert the depth frame to a numpy array
                depth_data = np.array(depth_frame)

                # Serialize the frame
                serialized_frame = pickle.dumps(depth_data)
                frame_size = struct.pack("!L", len(serialized_frame))

                # Send frame size and frame data
                conn.sendall(frame_size)
                conn.sendall(serialized_frame)

                # Wait for a key press for 1 millisecond and break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Stop camera capture and close the connection
            k4a_device.stop_cameras()

if __name__ == "__main__":
    send_kinect_feed()

import cv2
from django.shortcuts import render
from django.http import StreamingHttpResponse
from imutils.video import VideoStream
import imutils
import dlib

# Global variable to keep track of streaming status
streaming = False

# Load the face detection model (you may need to download it)
face_detector = dlib.get_frontal_face_detector()

def generate_frames():
    vs = VideoStream(src=1, backend=cv2.CAP_DSHOW).start()


    while streaming:
        frame = vs.read()
        frame = imutils.resize(frame, width=800)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector(gray)

        for face in faces:
            # Add age and gender detection logic here
            # You may need to use a pre-trained model or API for age and gender prediction

            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

def webcam_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    global streaming
    if request.method == 'POST':
        streaming = not streaming
    return render(request, 'index.html')

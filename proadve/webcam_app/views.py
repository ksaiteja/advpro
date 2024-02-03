import mimetypes
import os
from django.utils import timezone
from django.conf import settings
from django.shortcuts import render
import cv2
from django.http import HttpResponse, StreamingHttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def index(request):
    return render(request, 'index.html')

def highlightFace(net, frame, conf_threshold=0.7):
    frameOpencvDnn=frame.copy()
    frameHeight=frameOpencvDnn.shape[0]
    frameWidth=frameOpencvDnn.shape[1]
    blob=cv2.dnn.blobFromImage(frameOpencvDnn, 1.0, (300, 300), [104, 117, 123], True, False)

    net.setInput(blob)
    detections=net.forward()
    faceBoxes=[]
    for i in range(detections.shape[2]):
        confidence=detections[0,0,i,2]
        if confidence>conf_threshold:
            x1=int(detections[0,0,i,3]*frameWidth)
            y1=int(detections[0,0,i,4]*frameHeight)
            x2=int(detections[0,0,i,5]*frameWidth)
            y2=int(detections[0,0,i,6]*frameHeight)
            faceBoxes.append([x1,y1,x2,y2])
            cv2.rectangle(frameOpencvDnn, (x1,y1), (x2,y2), (0,255,0), int(round(frameHeight/150)), 8)
    return frameOpencvDnn, faceBoxes

def gen_frames(request):
    faceNet = cv2.dnn.readNet("../models/opencv_face_detector_uint8.pb", "../models/opencv_face_detector.pbtxt")
    ageNet = cv2.dnn.readNet("../models/age_net.caffemodel", "../models/age_deploy.prototxt")
    genderNet = cv2.dnn.readNet("../models/gender_net.caffemodel", "../models/gender_deploy.prototxt")

    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
    ageList = ['(0-2)', '(4-6)', '(8-12)', '(15-24)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
    genderList = [ 'male','female']

    camera = cv2.VideoCapture(0)
    padding = 20

    prev_value = None  

    while True:
        success, frame = camera.read()
        if not success:
            break
        gender_age_info = {}
        resultImg, faceBoxes = highlightFace(faceNet, frame)
        if faceBoxes:
            for faceBox in faceBoxes:
                face = frame[max(0, faceBox[1] - padding): min(faceBox[3] + padding, frame.shape[0] - 1),
                       max(0, faceBox[0] - padding): min(faceBox[2] + padding, frame.shape[1] - 1)]

                blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

                genderNet.setInput(blob)
                genderPreds = genderNet.forward()
                gender = genderList[genderPreds[0].argmax()]

                ageNet.setInput(blob)
                agePreds = ageNet.forward()
                age = ageList[agePreds[0].argmax()]

                gender_age_info['gender']=gender
                gender_age_info['age']=age

                if prev_value != gender_age_info:
                    request.session['gender_age_info'] = gender_age_info
                    prev_value = gender_age_info
                    advertisement(request=request)
                    
                cv2.putText(resultImg, f'{gender}, {age}', (faceBox[0], faceBox[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', resultImg)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def send_advertisement_update(gender_age_info):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "advertisement_group",
        {
            "type": "send.advertisement.update",
            "advertisement_path": get_advertisement_image_path(gender_age_info),
        },
    )



def webcam_feed(request):
    return StreamingHttpResponse(gen_frames(request), content_type="multipart/x-mixed-replace;boundary=frame")
    
def file_iterator(file_path, chunk_size=8192):
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data
def advertisement(request):
    gender_age_info = request.session.get('gender_age_info')    
    if gender_age_info is not None:
        advertisement_image_path = get_advertisement_image_path(gender_age_info)
        print(advertisement_image_path)
        with open(advertisement_image_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/jpeg')
    else:
        advertisement_image_path = get_advertisement_image_path({'gender': 'default', 'age': '(0-0)'})
        with open(advertisement_image_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/jpeg')
    
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

    

def get_advertisement_image_path(gender_age_info):
    if(not gender_age_info):
        image_path = 'advertisements\default-(0-0).jpg'
        return image_path
    gender = gender_age_info['gender']
    # gender="male"
    age = gender_age_info['age']
    # age='(15-20)'
    image_path = f'advertisements\{gender.lower()}-{age}.jpg'
    full_image_path = os.path.join(settings.BASE_DIR, 'webcam_app', image_path)
    return full_image_path
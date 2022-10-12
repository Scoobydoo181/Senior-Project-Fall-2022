import cv2
from enum import Enum
import numpy as np

def centerCoordinates(f):
    '''Decorator function to convert corner coordinates to center coordinates'''
    def inner(*args, **kwargs):
        eyes = f(*args, **kwargs)
        return [tupleAdd((x, y), w/2, h/2) for (x, y, w, h) in eyes]
    return inner

def filterFalsePositives(f):
    '''Decorator function to filter out false positives'''
    def inner(*args, **kwargs):
        eyes = f(*args, **kwargs)
        if len(eyes) > 2:
            return list(sorted(eyes, key=lambda eye: eye[1] if len(eye) > 1 else eye)[:2])
        return eyes
    return inner

def tupleAdd(tup, a, b):
    '''Utility function to add two values to a tuple'''
    if len(tup) == 2:
        return (round(tup[0] + a), round(tup[1] + b))

    return tup

def getPupils(pupils, eyes):
    '''If a pupil is not detected, use the center of the eye instead'''
    return [tupleAdd(pupil[0].pt, x, y) if len(pupil) > 0 else tupleAdd((x, y), w/2, h/2) for pupil, (x, y, w, h) in zip(pupils, eyes)]

class EyeDetection:
    '''Class to manage eye detection'''
    class DetectionType(Enum):
        '''Enum to represent eye detection types'''
        EYE_CASCADE = 1
        EYE_CASCADE_BLOB = 2
        FACE_EYE_CASCADE = 3
        FACE_EYE_CASCADE_BLOB = 4

    def __init__(self):
        '''Load all the pretrained models needed for eye detection '''
        detectorParams = cv2.SimpleBlobDetector_Params()
        self.blobDetector = cv2.SimpleBlobDetector_create(detectorParams)

        # Source: https://github.com/opencv/opencv/tree/master/data/haarcascades
        self.eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
        self.faceDetector = cv2.CascadeClassifier("resources/haarcascade_frontalface_default.xml")

        self.detectionType = EyeDetection.DetectionType.FACE_EYE_CASCADE_BLOB

    def setDetectionType(self, detectionType):
        '''Set the detection type to the specified enum value'''
        self.detectionType = detectionType

    @filterFalsePositives
    def detectEyes(self, image):
        '''Returns the coordinates of the eyes in the image using the specified detector'''
        if self.detectionType == EyeDetection.DetectionType.EYE_CASCADE:
            return self.eyeCascadeDetector(image)

        elif self.detectionType == EyeDetection.DetectionType.EYE_CASCADE_BLOB:
            return self.eyeCascadeBlobDetector(image)

        elif self.detectionType == EyeDetection.DetectionType.FACE_EYE_CASCADE:
            return self.faceEyeCascadeDetector(image)

        elif self.detectionType == EyeDetection.DetectionType.FACE_EYE_CASCADE_BLOB:
            return self.faceEyeCascadeBlobDetector(image)

    @centerCoordinates
    def eyeCascadeDetector(self, image):
        '''Detect eyes using a single Haar cascade detector'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return self.eyeDetector.detectMultiScale(gray)

    def eyeCascadeBlobDetector(self, image, demo=False):
        '''Detect eyes using a Haar cascade detector and blob detection'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if demo:
            cv2.imshow("Gray", gray)
            cv2.waitKey()

        eyes = self.eyeDetector.detectMultiScale(gray)
        croppedEyes = [gray[y:y+h, x:x+w] for (x, y, w, h) in eyes]
        if demo:
            for i, eye in enumerate(croppedEyes):
                cv2.imshow(f"Eye {i}", eye)
            cv2.waitKey()

        eyes_bw = [cv2.threshold(eye, 45, 255, cv2.THRESH_BINARY)[1]
                for eye in croppedEyes]

        if demo:
            for i, eye in enumerate(eyes_bw):
                cv2.imshow(f"Binary {i}", eye)
            cv2.waitKey()

        eyes_bw = [cv2.medianBlur(cv2.dilate(cv2.erode(
            eye, None, iterations=2), None, iterations=4), 5) for eye in eyes_bw]


        pupils = [self.blobDetector.detect(eye) for eye in eyes_bw]
        if demo:
            for i, (eye, pupil) in enumerate(zip(eyes_bw, pupils)):
                cv2.imwrite(f"pupil{i}.jpg", eye)
                detected = cv2.drawKeypoints(
                    eye, pupil, eye, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                cv2.imshow(f"Blob {i} detected", detected)
            cv2.waitKey()

        return getPupils(pupils, eyes)


    def faceEyeCascadeDetector(self, image):
        '''Detect eyes using a face Haar cascade detector, an eye Haar cascade detector'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = self.faceDetector.detectMultiScale(gray)
        if len(faces) == 0:
            return []

        face = max(faces, key=lambda box: box[2]*box[3])

        faceX, faceY, faceW, faceH = face
        croppedFace = gray[faceY:faceY+faceH, faceX:faceX+faceW]

        eyes = self.eyeDetector.detectMultiScale(croppedFace)

        return [tupleAdd((x+w/2, y+h/2), faceX, faceY) for (x, y, w, h) in eyes]

    def faceEyeCascadeBlobDetector(self, image):
        '''Detect eyes using a face Haar cascade detector, an eye Haar cascade detector, and blob detection'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = self.faceDetector.detectMultiScale(gray)
        if len(faces) == 0:
            return []

        face = max(faces, key=lambda box: box[2]*box[3])

        faceX, faceY, faceW, faceH = face
        croppedFace = gray[faceY:faceY+faceH, faceX:faceX+faceW]

        eyes = self.eyeDetector.detectMultiScale(croppedFace)
        croppedEyes = [gray[y:y+h, x:x+w] for (x, y, w, h) in eyes]

        eyes_bw = [cv2.threshold(eye, 45, 255, cv2.THRESH_BINARY)[1]
                for eye in croppedEyes]

        eyes_bw = [cv2.medianBlur(cv2.dilate(cv2.erode(
            eye, None, iterations=2), None, iterations=4), 5) for eye in eyes_bw]

        pupils = [self.blobDetector.detect(eye) for eye in eyes_bw]

        return [tupleAdd(pupil, faceX, faceY) for pupil in getPupils(pupils, eyes)]


def testRealtimeEyeDetection():
    '''Test the eye detection algorithms live on a webcam'''

    camera = cv2.VideoCapture(0)
    detector = EyeDetection()

    while(True):
        _, image = camera.read()

        eyes = detector.detectEyes(image)

        # if len(eyes) == 0:
        #     print("No eyes detected")

        for eye in eyes:
            if len(eye) == 2:
                cv2.circle(image, (eye[0], eye[1]), 7, (0, 0, 255), 2)
        cv2.imshow("Eyes", image)
        if cv2.waitKey(delay=1) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()


def testDemoBlobDetection(demo=True):
    '''Run blob detection in demo mode to visualize each step of the process'''
    image = cv2.imread("sampleFace.jpg")

    eyeDetection = EyeDetection()

    eyeDetection.eyeCascadeBlobDetector(image, demo)


def testTakePicture():
    '''Test taking a picture with the webcam and saving it to a file'''
    camera = cv2.VideoCapture(0)
    _, img = camera.read()

    cv2.imwrite("sampleFace.jpg", img)
    camera.release()

def testPupilBlobDetection():
    '''Test the blob detection algorithm in isolation on extracted black and white eye images'''
    image = cv2.imread("pupil0.jpg")

    detectorParams = cv2.SimpleBlobDetector_Params()
    blobDetector = cv2.SimpleBlobDetector_create(detectorParams)

    pupil = blobDetector.detect(image)
    print(pupil[0].pt)

    detected = cv2.drawKeypoints(image, pupil, np.array([]), (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    detected = cv2.circle(detected, tupleAdd(pupil[0].pt, 0, 0), 7, (0, 0, 255), 2)
    cv2.imshow("Blob detected", detected)
    cv2.waitKey()


if __name__ == "__main__":
    testRealtimeEyeDetection()
    # testDemoBlobDetection()
    # testPupilBlobDetection()
    # testTakePicture()

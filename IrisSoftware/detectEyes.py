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

def getPupils(pupils, eyes, cropHeights):
    '''Add eye box and eyebrow crop coordinate offsets back in to transform the 
    pupil coordinates from the blob detector back to the original image'''

    return [tupleAdd(pupil[0].pt, x, y+cropHeight) for pupil, (x, y, w, h), cropHeight in zip(pupils, eyes, cropHeights) if len(pupil) > 0]

def preprocessEyeImage(image, numIterations=7):
    '''Preprocess a cropped black and white eye image to make it easier to detect the pupil'''
    for _ in range(numIterations):
        cv2.medianBlur(image, 5, image)
    
    return image

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

        self.blobThreshold = 45
        self.numBlurIterations = 7

    def setDetectionType(self, detectionType):
        '''Set the detection type to the specified enum value'''
        self.detectionType = detectionType

    def setBlobThreshold(self, threshold):
        '''Set the greyscale threshold used internally when converting images to black and white 
        for the blob detector. 
        
        Range: 0-255. 
        
        Pixels lower than the threshold will be set to 0 (black), 
        and pixels higher than the threshold will be set to 255 (white).
        
        Users with darker eye colors should user a lower threshold, 
        and users with ligher eye colors should user a higher threshold 
        to make sure the iris is captured in the blob detector'''
        self.blobThreshold = threshold

    def setNumBlurIterations(self, numIterations):
        '''Set the number of iterations to run the median blur filter on the image 
        before running the blob detector. 
        
        Increasing this value will reduce the amount of noise in the detection image, and enlarge the pupil area.'''
        self.numBlurIterations = numIterations

    def detectFace(self, image):
        '''Detect a face in the image'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.faceDetector.detectMultiScale(gray)
        return max(faces, key=lambda box: box[2]*box[3]) if len(faces) > 0 else None

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

    def eyeCascadeBlobDetector(self, image):
        '''Detect eyes using a Haar cascade detector and blob detection'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        eyes = self.eyeDetector.detectMultiScale(gray)
        croppedEyes = [gray[y:y+h, x:x+w] for (x, y, w, h) in eyes]

        eyes_bw = [cv2.threshold(eye, self.blobThreshold, 255, cv2.THRESH_BINARY)[1]
                for eye in croppedEyes]

        # Crop out eyebrows (top 1/4 of eye image)
        cropHeights = [eye.shape[0]//4 for eye in eyes_bw]
        eyes_bw = [eye[eye.shape[0]//4:, :] for eye in eyes_bw]

        eyes_processed = [preprocessEyeImage(eye, self.numBlurIterations) for eye in eyes_bw]

        pupils = [self.blobDetector.detect(eye) for eye in eyes_processed]

        return getPupils(pupils, eyes, cropHeights)


    def faceEyeCascadeDetector(self, image):
        '''Detect eyes using a face Haar cascade detector, and an eye Haar cascade detector'''
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        faces = self.faceDetector.detectMultiScale(gray)
        if len(faces) == 0:
            print("No face detected")
            return []

        face = max(faces, key=lambda box: box[2]*box[3])

        faceX, faceY, faceW, faceH = face
        croppedFace = gray[faceY:faceY+faceH, faceX:faceX+faceW]

        eyes = self.eyeDetector.detectMultiScale(croppedFace)

        return [tupleAdd((x+w/2, y+h/2), faceX, faceY) for (x, y, w, h) in eyes]

    def faceEyeCascadeBlobDetector(self, image, demo=False):
        '''Detect eyes using a face Haar cascade detector, an eye Haar cascade detector, and blob detection'''
        if demo:
            cv2.imwrite(f"image1_input.jpg", image)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if demo:
            cv2.imshow("Gray", gray)
            cv2.waitKey()
            cv2.imwrite(f"image2_grayscale.jpg", gray)

        faces = self.faceDetector.detectMultiScale(gray)
        if len(faces) == 0:
            print("No face detected")
            return []

        face = max(faces, key=lambda box: box[2]*box[3])
        faceX, faceY, faceW, faceH = face
        croppedFace = gray[faceY:faceY+faceH, faceX:faceX+faceW]
        if demo:
            cv2.imshow(f"Cropped Face", croppedFace)
            cv2.waitKey()
            cv2.imwrite(f"image3_croppedFace.jpg", croppedFace)

        eyes = self.eyeDetector.detectMultiScale(croppedFace)
        croppedEyes = [croppedFace[y:y+h, x:x+w] for (x, y, w, h) in eyes]
        if demo:
            for i, eye in enumerate(croppedEyes):
                cv2.imshow(f"Eye {i}", eye)
                cv2.imwrite(f"image4_eye{i}.jpg", eye)
            cv2.waitKey()

        eyes_bw = [cv2.threshold(eye, self.blobThreshold, 255, cv2.THRESH_BINARY)[1] for eye in croppedEyes]
        if demo:
            for i, eye in enumerate(eyes_bw):
                cv2.imshow(f"Binary {i}", eye)
                cv2.imwrite(f"image5_binaryEye{i}.jpg", eye)
            cv2.waitKey()

        # Crop out eyebrows (top 1/4 of eye image)
        cropHeights = [eye.shape[0]//4 for eye in eyes_bw]
        eyes_bw = [eye[eye.shape[0]//4:, :] for eye in eyes_bw]
        if demo:
            for i, eye in enumerate(eyes_bw):
                cv2.imwrite(f"pupil{i}.jpg", eye)
                cv2.imwrite(f"image6_croppedEyebrows{i}.jpg", eye)
                cv2.imshow(f"Cropped Eyebrows {i}", eye)
            cv2.waitKey()

        eyes_processed = [preprocessEyeImage(eye, self.numBlurIterations) for eye in eyes_bw]
        if demo:
            for i, eye in enumerate(eyes_processed):
                cv2.imshow(f"Processed {i}", eye)
                cv2.imwrite(f"image7_processedEye{i}.jpg", eye)
            cv2.waitKey()

        pupils = [self.blobDetector.detect(eye) for eye in eyes_processed]
        if demo:
            for i, (eye, pupil) in enumerate(zip(eyes_processed, pupils)):
                detected = cv2.drawKeypoints(eye, pupil, eye, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                cv2.imshow(f"Blob {i} detected", detected)
                cv2.imwrite(f"image8_blobDetected{i}.jpg", detected)
            cv2.waitKey()

        return [tupleAdd(pupil, faceX, faceY) for pupil in getPupils(pupils, eyes, cropHeights)]


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


def testDemoBlobDetection():
    '''Run blob detection in demo mode to visualize each step of the process'''
    image = cv2.imread("sampleFace.jpg")

    eyeDetection = EyeDetection()

    eyeDetection.faceEyeCascadeBlobDetector(image, demo=True)


def testTakePicture():
    '''Test taking a picture with the webcam and saving it to a file'''
    camera = cv2.VideoCapture(0)
    _, img = camera.read()

    cv2.imwrite("sampleFace.jpg", img)
    camera.release()

def testPupilBlobDetection():
    '''Test the blob detection algorithm in isolation on extracted black and white eye images'''
    image = cv2.imread("pupil0.jpg")
    cv2.imshow("Eye", image)
    cv2.waitKey();

    detectorParams = cv2.SimpleBlobDetector_Params()
    blobDetector = cv2.SimpleBlobDetector_create(detectorParams)

    image_processed = preprocessEyeImage(image)
    cv2.imshow("Processed Eye", image_processed)
    cv2.waitKey()

    pupil = blobDetector.detect(image_processed)
    print(pupil[0].pt)

    detected = cv2.drawKeypoints(image, pupil, np.array([]), (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    detected = cv2.circle(detected, tupleAdd(pupil[0].pt, 0, 0), 7, (0, 0, 255), 2)
    cv2.imshow("Blob detected", detected)
    cv2.waitKey()


if __name__ == "__main__":
    testRealtimeEyeDetection()
    # testTakePicture()
    # testDemoBlobDetection()
    # testPupilBlobDetection()

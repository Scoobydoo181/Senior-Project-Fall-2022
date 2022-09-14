import cv2
from enum import Enum

def centerCoordinates(f):
    '''Decorator function to convert corner coordinates to center coordinates'''
    def inner(*args, **kwargs):
        eyes = f(*args, **kwargs)
        return [map(round, (x+w/2, y+h/2)) for (x, y, w, h) in sorted(eyes, key=lambda eye: eye[1])[:2]]
    return inner

class DetectionType(Enum):
    EYE_CASCADE = 1
    EYE_CASCADE_BLOB = 2
    FACE_EYE_CASCADE = 3
    FACE_EYE_CASCADE_BLOB = 4
    EIGENFACE = 4

def detectEyes(image, detectorType=DetectionType.EYE_CASCADE, eyeDetector=None, blobDetector=None, faceDetector=None):
    '''Returns the coordinates of the eyes in the image using the specified detector'''
    if detectorType == DetectionType.EYE_CASCADE:
        return eyeCascadeDetector(image, eyeDetector)

    elif detectorType == DetectionType.EYE_CASCADE_BLOB:
        return eyeCascadeBlobDetector(image, eyeDetector, blobDetector)

    elif detectorType == DetectionType.FACE_EYE_CASCADE:
        return faceEyeCascadeDetector(image, eyeDetector, faceDetector)

    elif detectorType == DetectionType.FACE_EYE_CASCADE_BLOB:
        return faceEyeCascadeBlobDetector(image, detector)

    elif detectorType == DetectionType.EIGENFACE:
        return eigenfaceDetector(image, detector)

    else:
        raise ValueError('Invalid detector type: {}'.format(detectorType))
    
@centerCoordinates
def eyeCascadeDetector(image, detector):
    '''Detect eyes using a single Haar cascade detector'''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return detector.detectMultiScale(gray)

def tupleAdd(tuple, a, b):
    print("Blob detected")
    return (round(tuple[0] + a), round(tuple[1] + b))

def eyeCascadeBlobDetector(image, eyeDetector, blobDetector, demo=False):
    '''Detect eyes using a Haar cascade detector and blob detection'''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if demo:
        cv2.imshow("Gray", gray)
        cv2.waitKey()
    
    eyes = eyeDetector.detectMultiScale(gray)
    croppedEyes = [gray[y:y+h, x:x+w] for (x, y, w, h) in eyes]
    if demo:
        for i, eye in enumerate(croppedEyes):
            cv2.imshow(f"Eye {i}", eye)
        cv2.waitKey()    

    eyes_bw = [cv2.threshold(eye, 45, 255, cv2.THRESH_BINARY)[1] for eye in croppedEyes]
    if demo:
        for i, eye in enumerate(eyes_bw):
            cv2.imshow(f"Binary {i}", eye)
        cv2.waitKey()

    pupils = [blobDetector.detect(eye) for eye in eyes_bw]
    if demo:
        for i, (eye, pupil) in enumerate(zip(eyes_bw, pupils)):
            detected = cv2.drawKeypoints(eye, pupil, eye, (0, 0, 255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            cv2.imshow(f"Blob {i} detected", detected )
        cv2.waitKey()

    return [tupleAdd(pupil[0].pt, x, y) if len(pupil) > 0 else (x + round(w/2), y + round(h/2)) for pupil, (x, y, w, h) in zip(pupils, eyes)]

def faceEyeCascadeDetector(image, detector):
    '''Detect eyes using a face Haar cascade detector, an eye Haar cascade detector'''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray)
    return faces

def faceEyeCascadeBlobDetector(image, detector):
    '''Detect eyes using a face Haar cascade detector, an eye Haar cascade detector, and blob detection'''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray)
    return faces

def eigenfaceDetector(image, detector):
    '''Detect eyes using an eigenface detector'''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return detector.detectMultiScale(gray)

def testMain():
    camera = cv2.VideoCapture(0)

    # Source: https://github.com/opencv/opencv/tree/master/data/haarcascades
    # faceDetector = cv2.CascadeClassifier("resources/haarcascade_frontalface_default.xml")
    eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")

    detector_params = cv2.SimpleBlobDetector_Params()
    detector_params.filterByArea = True
    detector_params.maxArea = 1500
    blobDetector = cv2.SimpleBlobDetector_create(detector_params)

    while(True):
        _, image = camera.read()

        eyes = detectEyes(image, DetectionType.EYE_CASCADE_BLOB, eyeDetector, blobDetector)
        for (x, y) in eyes:
            cv2.circle(image, (x, y), 7, (0, 0, 255), 2)
        cv2.imshow("Eyes", image)
        if cv2.waitKey(delay=1) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()

def testBlobDetection(demo=True):
    image = cv2.imread("sampleFace.jpg")

    eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
    
    detector_params = cv2.SimpleBlobDetector_Params()
    detector_params.filterByArea = True
    detector_params.maxArea = 1500
    blobDetector = cv2.SimpleBlobDetector_create(detector_params)

    eyeCascadeBlobDetector(image, eyeDetector, blobDetector, demo)

def takePicture():
    camera = cv2.VideoCapture(0)
    _, img = camera.read()

    cv2.imwrite("sampleFace.jpg", img)
    camera.release()

if __name__ == "__main__":
    testMain()
    # testBlobDetection()
    # takePicture()

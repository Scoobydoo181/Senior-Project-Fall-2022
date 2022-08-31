import cv2

def detectEyes(image, detector):
    '''Returns the coordinates of the eyes in the image.'''
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    eyes = detector.detectMultiScale(gray)

    return [map(round, (x+w/2, y+h/2)) for (x, y, w, h) in sorted(eyes, key=lambda eye: eye[1])[:2]]

if __name__ == "__main__":
    camera = cv2.VideoCapture(0)

    # Source: https://github.com/opencv/opencv/tree/master/data/haarcascades
    faceDetector = cv2.CascadeClassifier("resources/haarcascade_frontalface_default.xml")
    eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
    while(True):
        _, image = camera.read()
        
        eyes = detectEyes(image, eyeDetector)
        for (x, y) in eyes:
            cv2.circle(image, (x, y), 10, (0, 0, 255), 3)
        cv2.imshow("Eyes", image)
        if cv2.waitKey(delay=1) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()
        

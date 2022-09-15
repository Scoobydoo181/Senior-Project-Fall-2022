from ui.main import launch_ui_thread
from detectEyes import detectEyes

import cv2

def detectBlink(eyeCoords, blinkDuration):
    pass

def clickMouse(screenCoords):
    pass

def moveMouse(screenCoords):
    pass

def menuKeyPressed():
    pass

def readSettingsFromUI():
    pass

if __name__ == "__main__":
    camera = cv2.VideoCapture(0)
    eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
    uiLaunched = false
    settings = {}

    blinkDuration = 0
    while True:
        if uiLaunched:
            readSettingsFromUI(settings)

        _, image = camera.read()

        eyeCoords = detectEyes(image, eyeDetector)

        didBlink = detectBlink(eyeCoords, blinkDuration)

        screenCoords = computeScreenCoords(eyeCoords)

        if didBlink:
            clickMouse(screenCoords)

        moveMouse(eyeCoords)

        if menuKeyPressed():
            launchUIThread()
            uiLaunched = True


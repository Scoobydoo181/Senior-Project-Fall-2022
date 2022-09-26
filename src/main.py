import pyautogui
import cv2
from detectEyes import detectEyes
from ui.runners import launchUIThread


def detectBlink(eyeCoords, blinkDuration):
    pass


def clickMouse(screenCoords):
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

        # [(x1, y1), (x2, y2), ...]
        eyeCoords = detectEyes(image, eyeDetector)

        didBlink = detectBlink(eyeCoords, blinkDuration)

        x, y = computeScreenCoords(eyeCoords)

        if didBlink:
            clickMouse(screenCoords)

        # Move mouse
        pyautogui.moveTo(x, y)

        if menuKeyPressed():
            launchUIThread()
            uiLaunched = True

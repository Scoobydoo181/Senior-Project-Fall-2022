"""Main file holding code responsible for running the program."""
from threading import Thread
import os
import pickle
import cv2
from detectEyes import detectEyes
from ui.runners import launchUIThread
from ui.widgets import CALIBRATION_FILE_NAME


class IrisSoftware:
    """Main class responsible for running the program."""

    def __init__(self) -> None:
        # State
        self.isCalibrated = False

    def run(self) -> None:
        # Check for calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            self.isCalibrated = True
            with open(CALIBRATION_FILE_NAME, "rb") as handle:
                print(pickle.load(handle))
        # Launch threads
        uiThread = Thread(target=launchUIThread)
        uiThread.start()


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
    # camera = cv2.VideoCapture(0)
    # eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
    # uiLaunched = false
    # settings = {}

    # blinkDuration = 0
    # while True:
    #     if uiLaunched:
    #         readSettingsFromUI(settings)

    #     _, image = camera.read()

    #     eyeCoords = detectEyes(image, eyeDetector)

    #     didBlink = detectBlink(eyeCoords, blinkDuration)

    #     screenCoords = computeScreenCoords(eyeCoords)

    #     if didBlink:
    #         clickMouse(screenCoords)

    #     moveMouse(eyeCoords)

    #     if menuKeyPressed():
    #         launchUIThread()
    #         uiLaunched = True
    program = IrisSoftware()
    program.run()

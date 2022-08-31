from detectEyes import detectEyes
from ui import launchMenuThread

def getCameraImage(camera):
    pass

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
    camera = None
    eyeDetector = None
    uiLaunched = false
    settings = {}

    blinkDuration = 0
    while True:
        if uiLaunched:
            readSettingsFromUI(settings)

        image = getCameraImage(camera)

        eyeCoords = detectEyes(image, eyeDetector)

        didBlink = detectBlink(eyeCoords, blinkDuration)

        screenCoords = computeScreenCoords(eyeCoords)

        if didBlink:
            clickMouse(screenCoords)

        moveMouse(eyeCoords)

        if menuKeyPressed():
            launchUIThread()
            uiLaunched = True


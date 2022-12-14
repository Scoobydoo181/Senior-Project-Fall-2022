"""Main file holding code responsible for running the program."""
import os
import pickle
import sys
import threading
import cv2
import pyautogui
from detectEyes import EyeDetection
from computeScreenCoords import Interpolator, InterpolationType
from ui import (
    UI,
    CALIBRATION_FILE_NAME,
    PupilModelOptions,
    EYE_COLOR_THRESHOLD_RANGE,
    DEFAULT_EYE_COLOR_THRESHOLD,
)
from camera import Camera
from settings import loadSettings, saveSettings, SETTINGS_FILE_NAME


class IrisSoftware:
    """Main class responsible for running the program."""

    class State:
        """Wrapper for program state."""

        def __init__(self) -> None:
            self.shouldExit = False
            self.isCalibrated = False
            self.currentlyCalibrating = False
            self.calibrationEyeCoords: list[list[tuple]] = []
            self.faceBoxes = []
            self.faceBox = None
            self.lastCursorPos = pyautogui.position()
            self.skipMouseMovement = False
            self.interpolatorType = InterpolationType.JOYSTICK

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        self.settings = loadSettings()
        self.state = IrisSoftware.State()
        self.processingSem = threading.Semaphore()

        self.eyeDetector = EyeDetection()

        self.camera = Camera()

        self.ui = UI(self.camera.getResolution())
        self.ui.onCalibrationComplete = self.saveCalibrationData
        self.ui.onCaptureCalibrationEyeCoords = self.captureCalibrationEyeCoords
        self.ui.onCalibrationCancel = self.resetCalibrationEyeCoords
        self.ui.onChangePupilModel = self.changePupilModel
        self.ui.onChangeEyeColorThreshold = self.changeEyeColorThreshold
        self.ui.onCalibrationOpen = self.setCurrentlyCalibrating

        self.processingThread: threading.Thread

        self.interpolator = Interpolator()

        # Load calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            with open(CALIBRATION_FILE_NAME, "rb") as f:
                self.state.faceBox = pickle.load(f)["faceBox"]

            self.interpolator.calibrateInterpolator(
                CALIBRATION_FILE_NAME, self.state.interpolatorType
            )
            self.state.isCalibrated = True

    def moveMouse(self, screenX, screenY):
        """Move the mouse to the given screen coordinates, moving smoothly over multiple frames"""
        # Smooth out the mouse movement to minimize jitter
        smoothingFactor = 0.1

        x = self.state.lastCursorPos[0] + (
            (screenX - self.state.lastCursorPos[0]) * smoothingFactor
        )
        y = self.state.lastCursorPos[1] + (
            (screenY - self.state.lastCursorPos[1]) * smoothingFactor
        )

        if not self.state.skipMouseMovement:
            # print("Moving mouse from", pyautogui.position(), " to: ", (x, y), "goal coords: ", (screenX, screenY))
            pyautogui.moveTo(x, y)
            self.state.lastCursorPos = (x, y)

    def safeComputeCoords(self, eyeCoords):
        # return last cursor position if available when eyes aren't properly detected, if not return center screen
        if len(eyeCoords) < 2:
            self.state.skipMouseMovement = True
            return self.state.lastCursorPos

        newCoords = self.interpolator.computeScreenCoords(eyeCoords)

        if newCoords is not None:
            return newCoords
        else:
            self.state.skipMouseMovement = True
            return self.state.lastCursorPos

    def changeEyeColorThreshold(self, value: int):
        """Take a value within EYE_COLOR_THRESHOLD_RANGE and scale it up to a max of ~100."""
        rangeMax = EYE_COLOR_THRESHOLD_RANGE[1]
        step = 100 // rangeMax

        self.settings.eyeColorThreshold = value
        transformedValue = step * (value)
        print("Set detection threshold: ", transformedValue)
        self.eyeDetector.setBlobThreshold(transformedValue)
        saveSettings(self.settings)

    def changePupilModel(self, value: PupilModelOptions):
        self.settings.pupilDetectionModel = value
        if value == PupilModelOptions.ACCURACY:
            self.eyeDetector.setDetectionType(
                EyeDetection.DetectionType.FACE_EYE_CASCADE_BLOB
            )
        elif value == PupilModelOptions.SPEED:
            self.eyeDetector.setDetectionType(
                EyeDetection.DetectionType.EYE_CASCADE_BLOB
            )
        saveSettings(self.settings)

    def resetCalibrationEyeCoords(self):
        self.state.calibrationEyeCoords = []
        self.unsetCurrentlyCalibrating()
        print("Reset current calibration eye coords.")

    def captureCalibrationEyeCoords(self):
        """Captures and stores a eye coords for calibration."""
        eyeCoords = []
        maxFramesToCapture = 30

        for _ in range(maxFramesToCapture):
            frame = self.camera.getFrame()
            eyeCoords = self.eyeDetector.detectEyes(frame)
            if len(eyeCoords) >= 2:
                break

        if len(eyeCoords) < 2:
            eyeCoords = [(None, None), (None, None)]

        self.state.calibrationEyeCoords.append(eyeCoords)
        print(f"Captured calibration eye coords: {eyeCoords}")

        faceBox = self.eyeDetector.detectFace(frame)
        if faceBox is not None:
            self.state.faceBoxes.append(faceBox)

        self.ui.emitFinishedCaptureEyeCoords()

    def averageFaceBox(self, faceBoxes):
        """Averages the face box coordinates."""
        if len(faceBoxes) == 0:
            return None

        x = 0
        y = 0
        w = 0
        h = 0

        for faceBox in faceBoxes:
            x += faceBox[0]
            y += faceBox[1]
            w += faceBox[2]
            h += faceBox[3]

        return (
            round(x / len(faceBoxes)),
            round(y / len(faceBoxes)),
            round(w / len(faceBoxes)),
            round(h / len(faceBoxes)),
        )

    def saveCalibrationData(self):
        """Saves the current calibration data and trains the screen coords model."""
        # Remove the old calibration data, if it exists
        if os.path.exists(CALIBRATION_FILE_NAME):
            os.remove(CALIBRATION_FILE_NAME)

        # Add calibration circles' locations to calibration data
        calibrationCircleLocations = self.ui.calibrationWindow.getCircleLocations()
        calibrationData = {
            "eyeCoords": self.state.calibrationEyeCoords,
            "calibrationCircleLocations": calibrationCircleLocations,
            "faceBox": self.averageFaceBox(self.state.faceBoxes),
        }
        self.state.faceBox = self.averageFaceBox(self.state.faceBoxes)

        # Store calibration data in pickle file
        with open(CALIBRATION_FILE_NAME, "wb") as handle:
            pickle.dump(calibrationData, handle)

        print("Saved new calibration data.")

        # Train screen coords model
        self.interpolator.calibrateInterpolator(
            CALIBRATION_FILE_NAME, self.state.interpolatorType
        )

        self.state.isCalibrated = True

        # Reset current calibration frames
        self.resetCalibrationEyeCoords()

    def drawOnFrame(self, frame, eyeCoords):
        thickness = 2
        blue600 = (216, 78, 29)  # G,B,R
        white = (255, 255, 255)  # G,B,R

        # Draw circles around the eyes
        for (x, y) in eyeCoords:
            frame = cv2.circle(frame, (x, y), 10, blue600, thickness)

        if not self.state.isCalibrated:
            # Do not continue drawing data that requires calibration without being calibrated
            return frame

        # Draw the face box
        faceX, faceY, faceW, faceH = self.state.faceBox
        frame = cv2.rectangle(
            frame, (faceX, faceY), (faceX + faceW, faceY + faceH), white, thickness
        )

        if self.state.interpolatorType == InterpolationType.JOYSTICK:
            # Draw the eye boxes for Joystick mode
            topLeft, bottomRight = self.interpolator.getLeftEyeBox()
            frame = cv2.rectangle(frame, topLeft, bottomRight, white, thickness)

            topLeft, bottomRight = self.interpolator.getRightEyeBox()
            frame = cv2.rectangle(frame, topLeft, bottomRight, white, thickness)

        return frame

    def setCurrentlyCalibrating(self):
        self.processingSem.acquire()
        self.state.currentlyCalibrating = True

    def unsetCurrentlyCalibrating(self):
        self.state.currentlyCalibrating = False
        self.processingSem.release()

    def processing(self):
        """Thread to run main loop of eye detection"""
        while not self.state.shouldExit:
            if self.state.currentlyCalibrating:
                self.processingSem.acquire()
                self.processingSem.release()
                continue

            # Get the camera frame
            frame = self.camera.getFrame()

            # Get eye coordinates
            eyeCoords = self.eyeDetector.detectEyes(frame)

            # Draw borders on the frame
            frame = self.drawOnFrame(frame, eyeCoords)

            # Pass the frame to the UI
            self.ui.emitCameraFrame(frame)

            if not self.state.isCalibrated:
                # Do not run code that requires the program to be calibrated
                continue

            # Check for blinks
            didBlink = self.eyeDetector.detectBlink(eyeCoords)

            # Determine screen coordinates from eye coordinates
            screenX, screenY = self.safeComputeCoords(eyeCoords)

            # Click the mouse if the user has blinked
            if didBlink:
                print("Blink detected")
                pyautogui.click()

            # Move the mouse based on the eye coordinates
            self.moveMouse(screenX, screenY)
            self.state.skipMouseMovement = False

        # Release the camera before exiting
        self.camera.release()

    def run(self) -> None:
        """Launch threads and start program"""
        print("Starting Iris Software...")
        # Show instructions
        instructionsResult = self.ui.runShowInstructions()
        if instructionsResult == -1:
            sys.exit()
        # Spawn the processing thread
        print("Launching processing thread...")
        self.processingThread = threading.Thread(target=self.processing)
        self.processingThread.start()
        # Handle initial settings
        if not os.path.exists(SETTINGS_FILE_NAME):
            print("Performing initial configuration...")
            self.changeEyeColorThreshold(DEFAULT_EYE_COLOR_THRESHOLD)
            result = self.ui.runInitialConfiguration()
            if result == -1:
                self.state.shouldExit = True
                sys.exit()
        # Handle initial calibration
        if not self.state.isCalibrated:
            print("Calibrating program...")
            result = self.ui.runInitialCalibration()
            if result == -1:
                self.state.shouldExit = True
                sys.exit()
        # Run the UI
        print("Launching the UI...")
        self.ui.run()
        # Tell all threads to exit
        print("Exiting Iris Software...")
        self.state.shouldExit = True


if __name__ == "__main__":
    program = IrisSoftware()
    program.run()

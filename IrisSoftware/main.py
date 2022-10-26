"""Main file holding code responsible for running the program."""
import os
import pickle
import sys
import threading
import cv2
import pyautogui
import numpy as np
from detectEyes import EyeDetection
from computeScreenCoords import Interpolator, InterpolationType
from ui import UI, CALIBRATION_FILE_NAME, PupilModelOptions, CALIBRATION_GRID_N
from camera import Camera
from settings import loadSettings, saveSettings, SETTINGS_FILE_NAME

CALIBRATION_PROCESSING_LOCK = threading.Lock()
RESUME_PROCESSING_EVENT = threading.Event()


class IrisSoftware:
    """Main class responsible for running the program."""

    class State:
        """Wrapper for program state."""

        def __init__(self) -> None:
            self.shouldExit = False
            self.isCalibrated = False
            self.isCalibrating = False
            self.calibrationEyeCoordinates: list[list[tuple[float, float]]] = []
            self.calibrationCircleLocations: list[tuple[int, int]] = []
            self.faceBoxes = []
            self.faceBox = None
            self.lastCursorPos = pyautogui.position()
            self.skipMouseMovement = False
            self.interpolatorType = InterpolationType.TANGENT_LINEAR_REGRESSION

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        self.settings = loadSettings()
        self.state = IrisSoftware.State()

        self.eyeDetector = EyeDetection()

        self.camera = Camera()

        self.ui = UI(self.camera.getResolution())
        self.ui.onCalibrationOpen = self.setIsCalibrating
        self.ui.onCalibrationComplete = self.saveCalibrationData
        self.ui.onCaptureCalibrationData = self.captureCalibrationData
        self.ui.onCalibrationCancel = self.resetCalibrationState
        self.ui.onChangePupilModel = self.changePupilModel
        self.ui.onChangeEyeColorThreshold = self.changeEyeColorThreshold

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

    def setIsCalibrating(self):
        self.state.isCalibrating = True

    def detectBlink(self, eyeCoords, blinkDuration) -> any:
        pass

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
        """Take a value from 1-10 and scale it up."""
        self.settings.eyeColorThreshold = value
        transformedValue = 45 + 5 * (value - 1)
        self.eyeDetector.setBlobThreshold(transformedValue)
        print(f"Changed eye color threshold to {transformedValue}.")
        saveSettings(self.settings)

    def changePupilModel(self, value: PupilModelOptions):
        self.settings.pupilDetectionModel = value
        if value == PupilModelOptions.ACCURACY:
            self.eyeDetector.setDetectionType(
                EyeDetection.DetectionType.FACE_EYE_CASCADE_BLOB
            )
            print("Changed pupil detection model to FACE_EYE_CASCADE_BLOB.")
        elif value == PupilModelOptions.SPEED:
            self.eyeDetector.setDetectionType(
                EyeDetection.DetectionType.EYE_CASCADE_BLOB
            )
            print("Changed pupil detection model to EYE_CASCADE_BLOB.")
        saveSettings(self.settings)

    def resetCalibrationState(self):
        self.state.calibrationEyeCoordinates = []
        self.state.calibrationCircleLocations = []
        self.state.isCalibrating = False
        RESUME_PROCESSING_EVENT.set()
        print("Reset calibration state.")

    def performInitialConfiguration(self):
        """Adjusts the eye color threshold until it detects pupils."""
        detectedPupils = False
        framesToCapture = 10

        for i in range(1, 10):
            self.changeEyeColorThreshold(i)

            currDetectedEyeCoords = []

            # Capture multiple frames to improve accuracy
            for _ in range(framesToCapture):
                frame = self.camera.getFrame()
                eyeCoords = self.eyeDetector.detectEyes(frame)
                if len(eyeCoords) >= 2:
                    currDetectedEyeCoords.append(eyeCoords)

            # Ensure that eyeCoords are found in each frame
            if len(currDetectedEyeCoords) >= int(framesToCapture * 0.8):
                print(f"Initial configuration eye threshold: {i + 1}")
                self.changeEyeColorThreshold(i + 1)
                detectedPupils = True
                break

        if not detectedPupils:
            os.remove(SETTINGS_FILE_NAME)
            raise Exception(
                "Failed to detect any pupil data during initial configuration."
            )

    def processCalibrationFrames(self, frames: list[np.ndarray] = None):
        """Converts a list of lists of camera frames into median eye coordinates."""

        # Should never happen:
        if not frames:
            return

        leftEyeCoordinates: list[tuple[int, int]] = []
        rightEyeCoordinates: list[tuple[int, int]] = []

        # Collect coordinates
        CALIBRATION_PROCESSING_LOCK.acquire()
        for frame in frames:
            eyeCoords = self.eyeDetector.detectEyes(frame)
            if len(eyeCoords) == 2:
                leftEyeCoordinates.append(eyeCoords[0])
                rightEyeCoordinates.append(eyeCoords[1])
            faceBox = self.eyeDetector.detectFace(frame)
            if faceBox is not None:
                self.state.faceBoxes.append(faceBox)
        CALIBRATION_PROCESSING_LOCK.release()

        # Determine median
        medianCoordinates = [(None, None), (None, None)]
        if len(leftEyeCoordinates) > 0 and len(rightEyeCoordinates) > 0:
            leftEyeMedian = tuple(np.median(leftEyeCoordinates, axis=0))
            rightEyeMedian = tuple(np.median(rightEyeCoordinates, axis=0))
            medianCoordinates = [leftEyeMedian, rightEyeMedian]

        self.state.calibrationEyeCoordinates.append(medianCoordinates)

        print(f"Captured calibration eye coordinates: {medianCoordinates}.")

        if len(self.state.calibrationEyeCoordinates) == CALIBRATION_GRID_N**2:
            self.ui.emitCalibrationComplete()

    def captureCalibrationData(self, circleLocation: tuple[int, int]):
        """Captures camera frames and passes them to another thread to store."""
        numFrames = 10
        frames: list[np.ndarray] = []

        # Collect camera frames
        for _ in range(numFrames):
            frame = self.camera.getFrame()
            frames.append(frame)

        # Process/store data
        self.state.calibrationCircleLocations.append(circleLocation)
        th = threading.Thread(
            target=self.processCalibrationFrames, kwargs={"frames": frames}
        )
        th.start()

        self.ui.emitContinueCalibration()

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

        calibrationData = {
            "eyeCoords": self.state.calibrationEyeCoordinates,
            "calibrationCircleLocations": self.state.calibrationCircleLocations,
            "faceBox": self.averageFaceBox(self.state.faceBoxes),
        }
        self.state.faceBox = self.averageFaceBox(self.state.faceBoxes)

        # Store calibration data in pickle file
        with open(CALIBRATION_FILE_NAME, "wb") as handle:
            pickle.dump(calibrationData, handle)

        print("Saved new calibration data.")

        # Reset current calibration frames
        self.resetCalibrationState()

        # TODO: train screen coords model

    def processing(self):
        """Thread to run main loop of eye detection"""
        while not self.state.shouldExit:
            # Skip processing if in calibration
            if self.state.isCalibrating:
                RESUME_PROCESSING_EVENT.wait()
                RESUME_PROCESSING_EVENT.clear()

            # Get the camera frame
            frame = self.camera.getFrame()

            # Get eye coordinates
            eyeCoords = self.eyeDetector.detectEyes(frame)

            # Draw circles around the eyes
            for (x, y) in eyeCoords:
                cv2.circle(frame, (x, y), 7, (0, 0, 255), 2)

            # Draw the face box
            faceX, faceY, faceW, faceH = self.state.faceBox
            frame = cv2.rectangle(
                frame, (faceX, faceY), (faceX + faceW, faceY + faceH), (0, 0, 255), 2
            )

            # Pass the frame to the UI
            self.ui.emitCameraFrame(frame)

            # # Check for blinks
            # didBlink = self.detectBlink(eyeCoords, self.blinkDuration)

            # # Determine screen coordinates from eye coordinates
            screenX, screenY = self.safeComputeCoords(eyeCoords)

            # # Click the mouse if the user has blinked
            # if didBlink:
            #     clickMouse(screenX, screenY)

            # # Move the mouse based on the eye coordinates
            self.moveMouse(screenX, screenY)
            self.state.skipMouseMovement = False

        # Release the camera before exiting
        self.camera.release()

    def run(self) -> None:
        """Launch threads and start program"""
        print("Starting Iris Software...")
        # Handle initial settings
        if not os.path.exists(SETTINGS_FILE_NAME):
            print("Performing initial configuration...")
            self.performInitialConfiguration()
        # Handle initial calibration
        if not self.state.isCalibrated:
            print("Calibrating program...")
            result = self.ui.runInitialCalibration()
            if result == -1:
                sys.exit()
            self.interpolator.calibrateInterpolator()
            self.state.isCalibrated = True
        # Spawn the processing thread
        print("Launching processing thread...")
        self.processingThread = threading.Thread(target=self.processing)
        self.processingThread.start()
        # Run the UI
        print("Launching the UI...")
        self.ui.run()
        # Tell all threads to exit
        print("Exiting Iris Software...")
        self.state.shouldExit = True


if __name__ == "__main__":
    program = IrisSoftware()
    program.run()

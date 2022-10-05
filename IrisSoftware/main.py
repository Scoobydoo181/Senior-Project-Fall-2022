"""Main file holding code responsible for running the program."""
import os
import pickle
import sys
import threading
import cv2
from numpy import ndarray
import pyautogui
from detectEyes import detectEyes, DetectionType
from computeScreenCoords import computeScreenCoords
from ui import UI, CALIBRATION_FILE_NAME
from camera import Camera


class IrisSoftware:
    """Main class responsible for running the program."""

    class State:
        """Wrapper for program state."""

        def __init__(self) -> None:
            self.shouldExit = False
            self.isCalibrated = False
            self.calibrationEyeCoords: list[list[tuple]] = []

    class Config:
        """Wrapper for program config/settings.

        Placeholder for now until we simplify with enums.
        """

        def __init__(self) -> None:
            self.detectionType: DetectionType = DetectionType.EYE_CASCADE_BLOB

            self.detectorParams = cv2.SimpleBlobDetector_Params()
            self.detectorParams.filterByArea = True
            self.detectorParams.maxArea = 1500

            self.blinkDuration = 0

            self.eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
            self.blobDetector = cv2.SimpleBlobDetector_create(self.detectorParams)

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        self.state = IrisSoftware.State()
        self.config = IrisSoftware.Config()

        self.camera = Camera()

        self.ui = UI(self.camera.getResolution())
        self.ui.onCalibrationComplete = self.saveCalibrationData
        self.ui.onCaptureCalibrationEyeCoords = self.captureCalibrationEyeCoords
        self.ui.onCalibrationCancel = self.resetCalibrationEyeCoords

        self.processingThread: threading.Thread

        # Load calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            self.isCalibrated = True
            with open(CALIBRATION_FILE_NAME, "rb") as handle:
                # TODO: train screen coords interpolator
                pass

    def detectBlink(self, eyeCoords, blinkDuration) -> any:
        pass

    def clickMouse(self, screenX, screenY):
        pass

    def resetCalibrationEyeCoords(self):
        self.state.calibrationEyeCoords = []
        print("Reset current calibration eye coords.")

    def captureCalibrationEyeCoords(self):
        """Captures and stores a eye coords for calibration."""
        frame = self.camera.getFrame()
        eyeCoords = detectEyes(
            frame,
            self.config.detectionType,
            self.config.eyeDetector,
            self.config.blobDetector,
        )
        self.state.calibrationEyeCoords.append(eyeCoords)
        print("Captured calibration eye coords.")

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
        }

        # Store calibration data in pickle file
        with open(CALIBRATION_FILE_NAME, "wb") as handle:
            pickle.dump(calibrationData, handle)

        print("Saved new calibration data.")

        # Reset current calibration frames
        self.resetCalibrationEyeCoords()

        # TODO: train screen coords model

    def processing(self):
        while not self.state.shouldExit:
            # Get the camera frame
            frame = self.camera.getFrame()
            # Get eye coordinates
            eyeCoords = detectEyes(
                frame,
                self.config.detectionType,
                self.config.eyeDetector,
                self.config.blobDetector,
            )

            # Draw circles around the eyes
            for (x, y) in eyeCoords:
                cv2.circle(frame, (x, y), 7, (0, 0, 255), 2)

            # Pass the frame to the UI
            self.ui.emitCameraFrame(frame)

            # # Check for blinks
            # didBlink = self.detectBlink(eyeCoords, self.blinkDuration)

            # # Determine screen coordinates from eye coordinates
            # screenX, screenY = computeScreenCoords(eyeCoords)

            # # Click the mouse if the user has blinked
            # if didBlink:
            #     clickMouse(screenX, screenY)

            # # Move the mouse based on the eye coordinates
            # pyautogui.moveTo(screenX, screenY)
        # TODO: handle any teardown steps

    def run(self) -> None:
        print("Starting Iris Software...")
        # Handle initial calibration
        if not self.isCalibrated:
            print("Calibrating program...")
            result = self.ui.runInitialCalibration()
            if result == -1:
                sys.exit()
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

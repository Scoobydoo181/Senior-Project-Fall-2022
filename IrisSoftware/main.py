"""Main file holding code responsible for running the program."""
import os
import pickle
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

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        # Properties, config, & state
        self.shouldExit = False
        self.isCalibrated = False
        self.settings = {}
        self.currentCalibrationFrames: list[ndarray] = []
        # TODO: we should put the following inside of a class for detectEyes
        self.blinkDuration = 0
        self.eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
        self.detectorParams = cv2.SimpleBlobDetector_Params()
        self.detectorParams.filterByArea = True
        self.detectorParams.maxArea = 1500
        self.blobDetector = cv2.SimpleBlobDetector_create(self.detectorParams)
        # END TODO

        # Classes & objects
        self.camera = Camera()
        self.ui = UI(self.camera.getResolution())
        self.ui.onCalibrationComplete = self.saveCalibrationFrames
        self.ui.onCaptureCalibrationFrame = self.captureCalibrationFrame
        self.ui.onCalibrationCancel = self.resetCurrentCalibrationFrames

        # Threads
        self.processingThread: threading.Thread

        # Load any saved data

        # Load calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            self.isCalibrated = True
            with open(CALIBRATION_FILE_NAME, "rb") as handle:
                # TODO
                pass

    def detectBlink(self, eyeCoords, blinkDuration) -> any:
        pass

    def clickMouse(self, screenX, screenY):
        pass

    def getCurrentEyeCoords(self) -> list[list[tuple]]:
        # Get the camera frame
        frame = self.camera.getFrame()
        # Get eye coordinates
        eyeCoords = detectEyes(
            frame,
            DetectionType.EYE_CASCADE_BLOB,
            self.eyeDetector,
            self.blobDetector,
        )

        # Draw circles around the eyes
        for (x, y) in eyeCoords:
            cv2.circle(frame, (x, y), 7, (0, 0, 255), 2)

        return eyeCoords

    def resetCurrentCalibrationFrames(self):
        self.currentCalibrationFrames = []
        print("Reset current calibration frames.")

    def captureCalibrationFrame(self):
        """Captures and stores a calibration frame."""
        frame = self.getFrameWithEyeCoords()
        self.currentCalibrationFrames.append(frame)
        print("Captured calibration frame.")

    def saveCalibrationFrames(self):
        """Saves the current calibration frames and trains the screen coords model."""
        # Remove the old calibration data, if it exists
        if os.path.exists(CALIBRATION_FILE_NAME):
            os.remove(CALIBRATION_FILE_NAME)

        # Add calibration circles' locations to calibration data
        calibrationCircleLocations = self.ui.calibrationWindow.getCircleLocations()
        calibrationData = {'eyeCoords': self.currentCalibrationFrames, 'calibrationCircleLocations': calibrationCircleLocations}

        # Store calibration data in pickle file
        with open(CALIBRATION_FILE_NAME, "wb") as handle:
            pickle.dump(calibrationData, handle)

        print("Saved new calibration data.")

        # Reset current calibration frames
        self.resetCurrentCalibrationFrames()

        # TODO: train screen coords model

    def processing(self):
        while not self.shouldExit:
            # Get the camera frame
            frame = self.camera.getFrame()
            # Get eye coordinates
            eyeCoords = detectEyes(
                frame,
                DetectionType.EYE_CASCADE_BLOB,
                self.eyeDetector,
                self.blobDetector,
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
        # Spawn the processing thread
        print("Launching processing thread...")
        self.processingThread = threading.Thread(target=self.processing)
        self.processingThread.start()
        # Run the UI
        print("Launching the UI...")
        self.ui.run()
        # Tell all threads to exit
        print("Exiting Iris Software...")
        self.shouldExit = True


if __name__ == "__main__":
    program = IrisSoftware()
    program.run()

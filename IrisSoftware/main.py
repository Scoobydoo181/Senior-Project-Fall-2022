"""Main file holding code responsible for running the program."""
import os
import pickle
import threading
from typing import Any
from PySide6 import QtCore
import cv2
import pyautogui
from IrisSoftware.detectEyes import detectEyes, DetectionType
from IrisSoftware.computeScreenCoords import computeScreenCoords
from IrisSoftware.UI import UI, CALIBRATION_FILE_NAME
from IrisSoftware.Camera import Camera


class IrisSoftware:
    """Main class responsible for running the program."""

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        # Properties & config
        self.shouldExit = False
        self.isCalibrated = False
        self.settings = {}
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

        # Threads
        self.processingThread: threading.Thread

        # Load any saved data

        # Load calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            self.isCalibrated = True
            with open(CALIBRATION_FILE_NAME, "rb") as handle:
                # TODO
                pass

    def detectBlink(self, eyeCoords, blinkDuration) -> Any:
        pass

    def clickMouse(self, screenX, screenY):
        pass

    @QtCore.Slot()
    def handleNeedsCalibrationFrame(self):
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
        self.ui.emitReceivedCalibrationFrame(frame)

    @QtCore.Slot(list)
    def handleCalibrationFrames(self, frames):
        # Convert frames into eye coordinates
        eyeCoordsMatrix = []
        for frame in frames:
            eyeCoords = detectEyes(
                frame,
                DetectionType.EYE_CASCADE_BLOB,
                self.eyeDetector,
                self.blobDetector,
            )
            eyeCoordsMatrix.append(eyeCoords)

        # Remove the old calibration data, if it exists
        if os.path.exists(CALIBRATION_FILE_NAME):
            os.remove(CALIBRATION_FILE_NAME)

        # Store calibration data in pickle file
        with open(CALIBRATION_FILE_NAME, "wb") as handle:
            pickle.dump(eyeCoordsMatrix, handle)

        # Close calibration window
        self.ui.emitCloseCalibrationWidget()

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
            self.ui.emitReceivedCameraFrame(frame)

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
        # Connect IPC event handlers
        print("Connecting UI callbacks...")
        self.ui.connectCalibrationFramesCallback(self.handleCalibrationFrames)
        self.ui.connectNeedsCalibrationFrameCallback(self.handleNeedsCalibrationFrame)
        # Run the UI
        print("Launching the UI...")
        self.ui.run()
        # Tell all threads to exit
        print("Exiting Iris Software...")
        self.shouldExit = True


if __name__ == "__main__":
    program = IrisSoftware()
    program.run()

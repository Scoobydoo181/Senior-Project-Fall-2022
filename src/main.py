"""Main file holding code responsible for running the program."""
import os
import pickle
from typing import Any
from PySide6 import QtCore
from numpy import ndarray
import cv2
from detectEyes import detectEyes, DetectionType
from computeScreenCoords import computeScreenCoords
from ui.UI import UI, CALIBRATION_FILE_NAME


class IrisSoftware:
    """Main class responsible for running the program."""

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        # Properties & config
        self.isCalibrated = False
        self.settings = {}
        self.blinkDuration = 0
        self.eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
        self.detectorParams = cv2.SimpleBlobDetector_Params()
        self.detectorParams.filterByArea = True
        self.detectorParams.maxArea = 1500
        self.blobDetector = cv2.SimpleBlobDetector_create(self.detectorParams)
        # Classes & objects
        self.ui = UI()

    def detectBlink(self, eyeCoords, blinkDuration) -> Any:
        pass

    def clickMouse(self, screenCoords):
        pass

    def moveMouse(self, screenCoords):
        pass

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

    @QtCore.Slot(ndarray)
    def handleCameraFrame(self, frame):
        """Runs every time the camera receives a frame."""
        # Get eye coordinates
        eyeCoords = detectEyes(
            frame, DetectionType.EYE_CASCADE_BLOB, self.eyeDetector, self.blobDetector
        )

        # Draw circles around the eyes
        for (x, y) in eyeCoords:
            cv2.circle(frame, (x, y), 7, (0, 0, 255), 2)

        # Return adjusted frame to UI
        self.ui.emitAdjustedCameraFrame(frame)

        # # Check for blinks
        # didBlink = self.detectBlink(eyeCoords, self.blinkDuration)

        # # Determine screen coordinates from eye coordinates
        # screenCoords = self.computeScreenCoords(eyeCoords)

        # # Click the mouse if the user has blinked
        # if didBlink:
        #     clickMouse(screenCoords)

        # # Move the mouse based on the eye coordinates
        # moveMouse(eyeCoords)

    def run(self) -> None:
        print("Starting Iris Software...")
        # Check for calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            self.isCalibrated = True
            with open(CALIBRATION_FILE_NAME, "rb") as handle:
                print(pickle.load(handle))
                # TODO: handle starting with calibration if the program is not calibrated yet
        # Connect IPC event handlers
        self.ui.connectCameraFrameCallback(self.handleCameraFrame)
        self.ui.connectCalibrationFramesCallback(self.handleCalibrationFrames)
        # Start the UI
        self.ui.run()


if __name__ == "__main__":
    program = IrisSoftware()
    program.run()

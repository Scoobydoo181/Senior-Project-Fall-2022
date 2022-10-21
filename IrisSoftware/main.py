"""Main file holding code responsible for running the program."""
import os
import pickle
import sys
import threading
import cv2
from numpy import ndarray
import pyautogui
from detectEyes import EyeDetection
from computeScreenCoords import Interpolator
from ui import UI, CALIBRATION_FILE_NAME, PupilModelOptions
from camera import Camera


class IrisSoftware:
    """Main class responsible for running the program."""

    class State:
        """Wrapper for program state."""

        def __init__(self) -> None:
            self.shouldExit = False
            self.isCalibrated = False
            self.calibrationEyeCoords: list[list[tuple]] = []
            self.lastCursorPos = None

    def __init__(self) -> None:
        print("Initializing Iris Software...")
        self.state = IrisSoftware.State()

        self.eyeDetector = EyeDetection()

        self.camera = Camera()

        self.ui = UI(self.camera.getResolution())
        self.ui.onCalibrationComplete = self.saveCalibrationData
        self.ui.onCaptureCalibrationEyeCoords = self.captureCalibrationEyeCoords
        self.ui.onCalibrationCancel = self.resetCalibrationEyeCoords
        self.ui.onChangePupilModel = self.changePupilModel
        self.ui.onChangeEyeColorThreshold = self.changeEyeColorThreshold

        self.processingThread: threading.Thread

        self.interpolator = Interpolator()

        # Load calibration data
        if os.path.exists(CALIBRATION_FILE_NAME):
            self.state.isCalibrated = True
            self.interpolator.calibrateInterpolator(CALIBRATION_FILE_NAME)

    def detectBlink(self, eyeCoords, blinkDuration) -> any:
        pass

    def moveMouse(self, screenX, screenY):
        """Move the mouse to the given screen coordinates, moving smoothly over multiple frames"""
        if self.state.lastCursorPos is None:
            pyautogui.moveTo(screenX, screenY)
            self.state.lastCursorPos = (screenX, screenY)
        else:
            # Smooth out the mouse movement to minimize jitter
            x = (
                self.state.lastCursorPos[0]
                + (screenX - self.state.lastCursorPos[0]) * 0.1
            )
            y = (
                self.state.lastCursorPos[1]
                + (screenY - self.state.lastCursorPos[1]) * 0.1
            )

            pyautogui.moveTo(x, y)
            self.state.lastCursorPos = (x, y)

    def safeComputeCoords(self, eyeCoords):
        # return last cursor position if available when eyes aren't properly detected, if not return center screen
        if len(eyeCoords) < 2:
            if self.state.lastCursorPos is not None:
                return self.state.lastCursorPos
            res = list(self.camera.getResolution())
            return tuple([resolution // 2 for resolution in res])

        return self.interpolator.computeScreenCoords(eyeCoords)

    def changeEyeColorThreshold(self, value: int):
        """Take a value from 1-10 and scale it up."""
        transformedValue = 45 + 5 * (value - 1)
        self.eyeDetector.setBlobThreshold(transformedValue)

    def changePupilModel(self, value: PupilModelOptions):
        if value == PupilModelOptions.ACCURACY:
            self.eyeDetector.setDetectionType(
                EyeDetection.DetectionType.FACE_EYE_CASCADE_BLOB
            )
        elif value == PupilModelOptions.SPEED:
            self.eyeDetector.setDetectionType(
                EyeDetection.DetectionType.EYE_CASCADE_BLOB
            )

    def resetCalibrationEyeCoords(self):
        self.state.calibrationEyeCoords = []
        print("Reset current calibration eye coords.")

    def captureCalibrationEyeCoords(self):
        """Captures and stores a eye coords for calibration."""
        frame = self.camera.getFrame()
        eyeCoords = self.eyeDetector.detectEyes(frame)
        if len(eyeCoords) < 2:
            eyeCoords = [(None, None), (None, None)]
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
        """Thread to run main loop of eye detection"""
        while not self.state.shouldExit:
            # Get the camera frame
            frame = self.camera.getFrame()

            # Get eye coordinates
            eyeCoords = self.eyeDetector.detectEyes(frame)

            # Draw circles around the eyes
            for (x, y) in eyeCoords:
                cv2.circle(frame, (x, y), 7, (0, 0, 255), 2)

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
            # self.moveMouse(screenX, screenY)

        # Release the camera before exiting
        self.camera.release()

    def run(self) -> None:
        """Launch threads and start program"""
        print("Starting Iris Software...")
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

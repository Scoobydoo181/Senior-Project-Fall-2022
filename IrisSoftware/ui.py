"""Handles running the UI elements."""
import sys
from PySide6.QtWidgets import QApplication
from widgets import MainWindow, CalibrationWindow
from PySide6 import QtCore


CALIBRATION_FILE_NAME = "calibrationData.pickle"


class UI:
    """Responsible for handling the user interface."""

    def __init__(self, cameraResolution: tuple[int]) -> None:
        print("Initializing UI...")
        # Create app
        self.app = QApplication([])
        # Create windows
        self.mainWindow = MainWindow(cameraResolution)
        self.calibrationWindow: CalibrationWindow
        # Create callback properties
        self.onCaptureCalibrationFrame: callable
        self.onCalibrationComplete: callable
        # Connect signal handlers
        self.mainWindow.openCalibrationSignal.connect(self.__handleCalibrationOpen)
        print("UI initialized.")

    def run(self):
        self.mainWindow.show()
        print("UI running.")
        return self.app.exec()

    def closeCalibrationWindow(self):
        self.calibrationWindow.close()
        self.calibrationWindow = None

    def emitCameraFrame(self, frame):
        self.mainWindow.cameraFrameSignal.emit(frame)

    ### Signal handlers ###

    @QtCore.Slot()
    def __handleCalibrationOpen(self):
        # Create window
        self.calibrationWindow = CalibrationWindow()
        # Connect signal handlers
        self.calibrationWindow.cancelSignal.connect(self.__handleCalibrationCancel)
        self.calibrationWindow.completeSignal.connect(self.__handleCalibrationComplete)
        self.calibrationWindow.captureFrameSignal.connect(
            self.__handleCalibrationCaptureFrame
        )
        # Show the window
        self.calibrationWindow.showFullScreen()
        # Minimize the main window
        self.mainWindow.showMinimized()

    @QtCore.Slot()
    def __handleCalibrationCancel(self):
        # Close calibration window
        self.closeCalibrationWindow()
        # Show main window
        self.mainWindow.showNormal()

    @QtCore.Slot()
    def __handleCalibrationComplete(self):
        # Callback
        if self.onCalibrationComplete:
            self.onCalibrationComplete()
        # Close calibration window
        self.closeCalibrationWindow()
        # Show main window
        self.mainWindow.showNormal()

    @QtCore.Slot()
    def __handleCalibrationCaptureFrame(self):
        # Callback
        if self.onCaptureCalibrationFrame:
            self.onCaptureCalibrationFrame()

    ### ###


if __name__ == "__main__":
    ui = UI((640, 480))
    sys.exit(ui.run())

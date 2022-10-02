"""Handles running the UI elements."""
import sys
from PySide6.QtWidgets import QApplication
from widgets import MainWidget

CALIBRATION_FILE_NAME = "calibrationData.pickle"


class UI:
    """Responsible for handling the user interface."""

    def __init__(self, cameraResolution: tuple[int]) -> None:
        print("Initializing UI...")
        self.app = QApplication([])
        self.mainWidget = MainWidget(cameraResolution)

    def run(self):
        self.mainWidget.show()
        return self.app.exec()

    ### Slot connectors ###

    def connectNeedsCalibrationFrameCallback(self, cb):
        self.mainWidget.emittedNeedsCalibrationFrame.connect(cb)

    def connectCalibrationFramesCallback(self, cb):
        self.mainWidget.emittedCalibrationFrames.connect(cb)

    ### ###

    ### Signal emitters ###

    def emitReceivedCameraFrame(self, frame):
        self.mainWidget.receivedCameraFrame.emit(frame)

    def emitReceivedCalibrationFrame(self, frame):
        self.mainWidget.receivedCalibrationFrame.emit(frame)

    def emitCloseCalibrationWidget(self):
        self.mainWidget.receivedCloseCalibrationWindow.emit()

    ### ###


if __name__ == "__main__":
    ui = UI((640, 480))
    sys.exit(ui.run())

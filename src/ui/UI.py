"""Handles running the UI elements."""
import sys
from PySide6.QtWidgets import QApplication
from . import widgets

CALIBRATION_FILE_NAME = "calibrationData.pickle"


class UI:
    """Responsible for handling the user interface."""

    def __new__(cls):
        """Handles singleton."""
        if not hasattr(cls, "instance"):
            cls.instance = super(UI, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.app = QApplication([])
        self.mainWidget = widgets.MainWidget()

    def connectNeedsCalibrationFrameCallback(self, cb):
        self.mainWidget.emittedNeedsCalibrationFrame.connect(cb)

    def connectCalibrationFramesCallback(self, cb):
        self.mainWidget.emittedCalibrationFrames.connect(cb)

    def emitReceivedCameraFrame(self, frame):
        self.mainWidget.receivedCameraFrame.emit(frame)

    def emitReceivedCalibrationFrame(self, frame):
        self.mainWidget.receivedCalibrationFrame.emit(frame)

    def emitCloseCalibrationWidget(self):
        self.mainWidget.receivedCloseCalibrationWindow.emit()

    def run(self):
        self.mainWidget.show()
        return self.app.exec()


if __name__ == "__main__":
    ui = UI()
    sys.exit(ui.run())

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

    def connectCameraFrameCallback(self, cb):
        self.mainWidget.cameraFrameAvailable.connect(cb)

    def connectCalibrationFramesCallback(self, cb):
        self.mainWidget.calibrationFramesAvailable.connect(cb)

    def emitAdjustedCameraFrame(self, frame):
        self.mainWidget.adjustedCameraFrameAvailable.emit(frame)

    def emitCloseCalibrationWidget(self):
        self.mainWidget.shouldCloseCalibrationWindow.emit()

    def run(self):
        self.mainWidget.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    ui = UI()
    ui.run()

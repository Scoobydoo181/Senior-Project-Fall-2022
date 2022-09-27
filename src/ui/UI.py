"""Handles running the UI elements."""
import sys
from PySide6.QtWidgets import QApplication
from . import widgets


class UI:
    """Responsible for handling the user interface."""

    def __init__(self) -> None:
        self.app = QApplication([])
        self.mainWidget = widgets.MainWidget()

    def connectCameraFrameCallback(self, cb):
        self.mainWidget.cameraFrameAvailable.connect(cb)

    def emitAdjustedCameraFrame(self, frame):
        self.mainWidget.adjustedCameraFrameAvailable.emit(frame)

    def run(self):
        self.mainWidget.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    ui = UI()
    ui.run()

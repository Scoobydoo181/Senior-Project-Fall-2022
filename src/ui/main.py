"""Handles any UI elements on the screen."""
import sys
from PySide6.QtWidgets import QApplication
from ui.widgets import MainWidget


def launchUIThread():
    app = QApplication([])

    widget = MainWidget()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launchUIThread()

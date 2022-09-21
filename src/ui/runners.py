"""Handles running the UI elements."""
import sys
from PySide6.QtWidgets import QApplication
from widgets import MainWidget


def launchUIThread():
    app = QApplication([])

    widget = MainWidget()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launchUIThread()

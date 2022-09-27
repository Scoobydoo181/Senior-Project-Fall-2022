"""Handles running the UI elements."""
import sys
from PySide6.QtWidgets import QApplication
from . import widgets


def launchUIThread():
    app = QApplication([])

    widget = widgets.MainWidget()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launchUIThread()

"""Handles any UI elements on the screen."""
import sys
from PySide6.QtWidgets import QApplication
from widgets import MainWidget


def launch_ui_thread():
    app = QApplication([])

    widget = MainWidget(app.primaryScreen())
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launch_ui_thread()

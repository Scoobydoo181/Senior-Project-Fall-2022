"""Handles any UI elements on the screen."""
import sys
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout


class MainWidget(QMainWindow):
    """Main widget"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Iris Software")

        text = QLabel("Main Window",
                      alignment=QtCore.Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(text)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)


def launch_ui_thread():
    app = QApplication([])

    widget = MainWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    launch_ui_thread()

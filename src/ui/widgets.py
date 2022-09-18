"""A collection of widgets for the UI."""
from PySide6 import QtCore
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton


class MainWidget(QMainWindow):
    """Main widget showing the video stream in the corner."""
    width = 360
    height = 240

    @QtCore.Slot()
    def open_calibration_window(self):
        self.calibration_window = CalibrationWidget()
        self.calibration_window.showFullScreen()
        self.showMinimized()

    def __init__(self, primary_screen: QScreen):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software")

        # Set window always on top
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # Adjust the style
        self.setStyleSheet(
            "background-color: black; color: white")

        # Create placeholder text
        self.text = QLabel("Main Window",
                           alignment=QtCore.Qt.AlignCenter)
        # Create calibrate button
        self.calibrate_button = QPushButton("Calibrate")
        # Connect onClick
        self.calibrate_button.clicked.connect(self.open_calibration_window)

        # Create layout container
        layout = QVBoxLayout()
        # Add placeholder text to container
        layout.addWidget(self.text)
        # Add calibrate button to container
        layout.addWidget(self.calibrate_button)

        # Create main window
        central_widget = QWidget()
        # Add container to main window
        central_widget.setLayout(layout)

        # Set the main window
        self.setCentralWidget(central_widget)
        # Set the position and size of the main window
        self.setGeometry(primary_screen.geometry().width(
        ) - MainWidget.width, 0, MainWidget.width, MainWidget.height)
        # Lock the width and height of the window
        self.setFixedSize(MainWidget.width, MainWidget.height)


class CalibrationWidget(QMainWindow):
    """Full-screen window with calibration steps."""

    def __init__(self):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Create placeholder text
        self.text = QLabel("Calibration Window",
                           alignment=QtCore.Qt.AlignCenter)

        # Create layout container
        layout = QVBoxLayout()
        # Add placeholder text to container
        layout.addWidget(self.text)

        # Create main window
        central_widget = QWidget()
        # Add container to main window
        central_widget.setLayout(layout)

        # Set the main window
        self.setCentralWidget(central_widget)

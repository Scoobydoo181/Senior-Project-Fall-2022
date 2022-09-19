"""A collection of widgets for the UI."""
from typing import List, Tuple
from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QApplication


class MainWidget(QMainWindow):
    """Main widget showing the video stream in the corner."""
    width = 360
    height = 240

    @QtCore.Slot()
    def open_calibration_window(self):
        self.calibration_window = CalibrationWidget()
        self.calibration_window.showFullScreen()
        self.showMinimized()

    def __init__(self):
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
        self.setGeometry(QApplication.primaryScreen().availableGeometry().width(
        ) - MainWidget.width, 0, MainWidget.width, MainWidget.height)
        # Lock the width and height of the window
        self.setFixedSize(MainWidget.width, MainWidget.height)


class CalibrationWidget(QMainWindow):
    """Full-screen window with calibration steps."""

    def draw_circle(self, loc: Tuple[int]):
        self.circles.append(CalibrationCircle(self.central_widget, loc))

    def get_circle_locations(self):
        # Get the screen geometry
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        # Get the locations
        locs = []
        true_left = 0
        true_mid_x = screen_geometry.center().x() - CalibrationCircle.size / 2
        true_mid_y = screen_geometry.center().y() - CalibrationCircle.size / 2
        true_right = screen_geometry.right() - CalibrationCircle.size
        true_top = 0
        # NOTE: Not sure if this is because my laptop has a notch, but this isn't actually the bottom?
        true_bottom = screen_geometry.bottom() - CalibrationCircle.size - 35
        # Top
        locs.append((true_left, true_top))
        locs.append((true_mid_x, true_top))
        locs.append((true_right, true_top))
        # Middle
        locs.append((true_left, true_mid_y))
        locs.append((true_mid_x, true_mid_y))
        locs.append((true_right, true_mid_y))
        # Bottom
        locs.append((true_left, true_bottom))
        locs.append((true_mid_x, true_bottom))
        locs.append((true_right, true_bottom))

        return locs

    def __init__(self):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Create main window
        self.central_widget = QWidget()
        # Store calibration circles
        self.circles: List[CalibrationCircle] = []
        locs = self.get_circle_locations()
        for loc in locs:
            self.draw_circle(loc)

        # Set the main window
        self.setCentralWidget(self.central_widget)


class CalibrationCircle(QPushButton):
    """Circle with an active state and onClick handler."""
    active = False
    active_color = "blue"
    inactive_color = "gray"
    size = 80

    def toggle_active(self):
        self.active = not self.active
        self.set_style()

    def set_style(self):
        style = "border-radius: 40px; background-color: "

        if self.active:
            self.setStyleSheet(f"{style}{self.active_color};")
        else:
            self.setStyleSheet(f"{style}{self.inactive_color};")

    @QtCore.Slot()
    def handle_click(self):
        if self.active and self.on_click:
            self.on_click()

    def __init__(self, parent: QWidget, loc: Tuple[int], on_click=None):
        super().__init__("", parent)

        # Store onClick
        self.on_click = on_click
        # Set size
        (x, y) = loc
        self.setGeometry(x, y, self.size, self.size)
        # Set onClick
        self.clicked.connect(self.handle_click)
        # Set style
        self.set_style()

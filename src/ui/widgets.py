"""A collection of widgets for the UI."""
from typing import List, Tuple
from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QApplication


class MainWidget(QMainWindow):
    """Main widget showing the video stream in the corner."""
    width = 360
    height = 240

    @QtCore.Slot()
    def openCalibrationWindow(self):
        self.calibrationWindow = CalibrationWidget()
        self.calibrationWindow.showFullScreen()
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
        self.calibrateButton = QPushButton("Calibrate")
        # Connect onClick
        self.calibrateButton.clicked.connect(self.openCalibrationWindow)

        # Create layout container
        layout = QVBoxLayout()
        # Add placeholder text to container
        layout.addWidget(self.text)
        # Add calibrate button to container
        layout.addWidget(self.calibrateButton)

        # Create main window
        centralWidget = QWidget()
        # Add container to main window
        centralWidget.setLayout(layout)

        # Set the main window
        self.setCentralWidget(centralWidget)
        # Set the position and size of the main window
        self.setGeometry(QApplication.primaryScreen().availableGeometry().width(
        ) - MainWidget.width, 0, MainWidget.width, MainWidget.height)
        # Lock the width and height of the window
        self.setFixedSize(MainWidget.width, MainWidget.height)


class CalibrationWidget(QMainWindow):
    """Full-screen window with calibration steps."""

    def drawCircle(self, loc: Tuple[int]):
        self.circles.append(CalibrationCircle(self.centralWidget, loc))

    def getCircleLocations(self):
        # Get the screen geometry
        screenGeometry = QApplication.primaryScreen().availableGeometry()
        # Get the locations
        locs = []
        trueLeft = 0
        trueMidX = screenGeometry.center().x() - CalibrationCircle.size / 2
        trueMidY = screenGeometry.center().y() - CalibrationCircle.size / 2
        trueRight = screenGeometry.right() - CalibrationCircle.size
        trueTop = 0
        # NOTE: Not sure if this is because my laptop has a notch, but this isn't actually the bottom?
        trueBottom = screenGeometry.bottom() - CalibrationCircle.size - 35
        # Top
        locs.append((trueLeft, trueTop))
        locs.append((trueMidX, trueTop))
        locs.append((trueRight, trueTop))
        # Middle
        locs.append((trueLeft, trueMidY))
        locs.append((trueMidX, trueMidY))
        locs.append((trueRight, trueMidY))
        # Bottom
        locs.append((trueLeft, trueBottom))
        locs.append((trueMidX, trueBottom))
        locs.append((trueRight, trueBottom))

        return locs

    def __init__(self):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Create main window
        self.centralWidget = QWidget()
        # Store calibration circles
        self.circles: List[CalibrationCircle] = []
        locs = self.getCircleLocations()
        for loc in locs:
            self.drawCircle(loc)

        # Set the main window
        self.setCentralWidget(self.centralWidget)


class CalibrationCircle(QPushButton):
    """Circle with an active state and onClick handler."""
    active = False
    activeColor = "blue"
    inactiveColor = "gray"
    size = 80

    def toggleActive(self):
        self.active = not self.active
        self.setStyle()

    def setStyle(self):
        style = "border-radius: 40px; background-color: "

        if self.active:
            self.setStyleSheet(f"{style}{self.activeColor};")
        else:
            self.setStyleSheet(f"{style}{self.inactiveColor};")

    @QtCore.Slot()
    def handleClick(self):
        if self.active and self.onClick:
            self.onClick()

    def __init__(self, parent: QWidget, loc: Tuple[int], onClick=None):
        super().__init__("", parent)

        # Store onClick
        self.onClick = onClick
        # Set size
        (x, y) = loc
        self.setGeometry(x, y, self.size, self.size)
        # Set onClick
        self.clicked.connect(self.handleClick)
        # Set style
        self.setStyle()

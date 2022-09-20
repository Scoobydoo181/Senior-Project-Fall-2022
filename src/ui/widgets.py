"""A collection of widgets for the UI."""
from typing import List, Tuple
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QApplication, QHBoxLayout


class MainWidget(QMainWindow):
    """Main widget showing the video stream in the corner."""
    width = 360
    height = 240

    @QtCore.Slot()
    def closeCalibrationWindow(self):
        self.calibrationWindow.close()
        self.showMaximized()

    @QtCore.Slot()
    def openCalibrationWindow(self):
        self.calibrationWindow = CalibrationWidget()
        self.calibrationWindow.showFullScreen()
        self.calibrationWindow.complete.connect(self.closeCalibrationWindow)
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
    complete = QtCore.Signal()

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

    def drawCircles(self):
        # Create widget
        circlesWidget = QWidget()
        # Store calibration circles
        self.circles: List[CalibrationCircle] = []
        # Get the circle locations
        locs = self.getCircleLocations()
        # Draw the circles
        for loc in locs:
            circle = CalibrationCircle(circlesWidget, loc)
            self.circles.append(circle)
        # Set as the central widget
        self.setCentralWidget(circlesWidget)

    @QtCore.Slot()
    def beginCalibration(self):
        # Draw circles
        self.drawCircles()
        # Activate the first circle
        self.activeCircleIndex = 0
        self.circles[self.activeCircleIndex].toggleActive()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # If calibration has begun and the spacebar was pressed
        if self.activeCircleIndex is not None and event.key() == QtCore.Qt.Key_Space:
            # Check if calibration is complete
            if self.activeCircleIndex >= len(self.circles) - 1:
                # TODO: finish calibration
                self.complete.emit()
                return super().keyPressEvent(event)
            # Store and progress calibration
            # TODO: get pupil coordinates and store them
            self.circles[self.activeCircleIndex].setParent(None)
            self.activeCircleIndex += 1
            self.circles[self.activeCircleIndex].toggleActive()

        return super().keyPressEvent(event)

    def drawInstructions(self):
        # Create widget
        container = QWidget()
        instructionsWidget = QWidget(container)
        # Create layout container
        layout = QVBoxLayout()
        # Add title to layout
        title = QLabel("Calibration", alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        # Add instructions to layout
        instructions = QLabel("These are some instructions.")
        layout.addWidget(instructions)
        # Add container to widget
        instructionsWidget.setLayout(layout)
        # Add button to widget
        beginButton = QPushButton("Begin Calibration")
        beginButton.clicked.connect(self.beginCalibration)
        layout.addWidget(beginButton)
        # Position the widget
        instructionsWidget.setParent(container)
        (centerX, centerY) = QApplication.primaryScreen(
        ).availableGeometry().center().toTuple()
        (widgetWidth, widgetHeight) = instructionsWidget.size().toTuple()
        instructionsWidget.move(
            centerX - widgetWidth, centerY - widgetHeight - 35)
        # Set as the central widget
        self.setCentralWidget(container)

    def __init__(self):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Draw the instructions
        self.drawInstructions()


class CalibrationCircle(QPushButton):
    """Circle with an active state and onClick handler."""
    active = False
    activeColor = "blue"
    inactiveColor = "black"
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

    def __init__(self, parent: QWidget, loc: Tuple[int]):
        super().__init__("", parent)

        # Set size
        (x, y) = loc
        self.setGeometry(x, y, self.size, self.size)
        # Set style
        self.setStyle()

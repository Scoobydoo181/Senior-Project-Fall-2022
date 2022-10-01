"""A collection of widgets for the UI."""
import math
import sys
from typing import Any
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QApplication,
    QHBoxLayout,
)
import cv2
import qimage2ndarray
from numpy import ndarray


class MainWidget(QMainWindow):
    """Main widget showing the video stream in the corner."""

    TARGET_PREVIEW_HEIGHT = 480

    receivedCameraFrame = QtCore.Signal(ndarray)
    receivedCalibrationFrame = QtCore.Signal(tuple)
    receivedCloseCalibrationWindow = QtCore.Signal()

    emittedNeedsCalibrationFrame = QtCore.Signal()
    emittedCalibrationFrames = QtCore.Signal(list)

    @QtCore.Slot()
    def handleCloseCalibrationWindow(self):
        self.closeCalibrationWindow()

    @QtCore.Slot()
    def openCalibrationWindow(self):
        self.calibrationWindow = CalibrationWidget()
        self.calibrationWindow.showFullScreen()
        self.calibrationWindow.completed.connect(self.emitCalibrationData)
        self.calibrationWindow.cancelled.connect(self.handleCloseCalibrationWindow)
        self.calibrationWindow.shouldCaptureFrame.connect(
            self.captureCameraFrameForCalibration
        )
        self.showMinimized()

    @QtCore.Slot()
    def emitCalibrationData(self):
        self.emittedCalibrationFrames.emit(self.currentCalibrationFrames)

    @QtCore.Slot()
    def captureCameraFrameForCalibration(self):
        # Request camera frame
        self.emittedNeedsCalibrationFrame.emit()

    @QtCore.Slot(ndarray)
    def displayCameraFrame(self, frame):
        """This function references the following snippet: https://gist.github.com/bsdnoobz/8464000"""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (self.previewSize.width(), self.previewSize.height()))
        image = qimage2ndarray.array2qimage(frame)
        self.videoPreview.setPixmap(QtGui.QPixmap.fromImage(image))

    @QtCore.Slot(ndarray)
    def storeCalibrationFrame(self, frame):
        self.currentCalibrationFrames.append(frame)

    def closeCalibrationWindow(self):
        self.currentCalibrationFrames = []
        self.calibrationWindow.close()
        self.calibrationWindow = None
        self.showNormal()
        self.positionInTopRightCorner()

    def positionInTopRightCorner(self):
        self.move(
            QApplication.primaryScreen().availableGeometry().right()
            - self.width()
            - self.margin,
            QApplication.primaryScreen().availableGeometry().top() + self.margin,
        )

    def setupUI(self):
        # Create video preview
        self.videoPreview = QLabel()
        self.videoPreview.setFixedSize(self.previewSize)
        # Create calibrate button
        self.calibrateButton = QPushButton("Calibrate")
        # Connect onClick
        self.calibrateButton.clicked.connect(self.openCalibrationWindow)

        # Create layout container
        layout = QVBoxLayout()
        # Add placeholder text to container
        layout.addWidget(self.videoPreview)
        # Add calibrate button to container
        layout.addWidget(self.calibrateButton)

        # Create main window
        centralWidget = QWidget()
        # Add container to main window
        centralWidget.setLayout(layout)

        # Set the main window
        self.setCentralWidget(centralWidget)
        # Set the position and size of the main window
        self.positionInTopRightCorner()

    def setupSlotHandlers(self):
        self.receivedCameraFrame.connect(self.displayCameraFrame)
        self.receivedCalibrationFrame.connect(self.storeCalibrationFrame)
        self.receivedCloseCalibrationWindow.connect(self.handleCloseCalibrationWindow)

    def calculatePreviewSize(self, cameraResolution: tuple[int]) -> QtCore.QSize:
        factor = MainWidget.TARGET_PREVIEW_HEIGHT / float(cameraResolution[1])

        width = math.ceil(cameraResolution[0] * factor)

        print(f"Preview resolution: {width}x{MainWidget.TARGET_PREVIEW_HEIGHT}")

        return QtCore.QSize(width, MainWidget.TARGET_PREVIEW_HEIGHT)

    def __init__(self, cameraResolution: tuple[int]):
        # pylint: disable=no-member
        super().__init__()
        # Properties
        self.previewSize = self.calculatePreviewSize(cameraResolution)
        self.margin = 40
        self.currentCalibrationFrames = []

        # Initialize UI elements
        self.calibrationWindow: CalibrationWidget = None
        self.videoPreview: QLabel = None
        self.calibrateButton: QPushButton = None
        # Initialize camera elements
        self.capture: Any = None
        self.timer: QtCore.QTimer = None

        # Remove window title
        self.setWindowTitle("Iris Software")
        # Set window always on top
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        # Adjust the style
        self.setStyleSheet("background-color: black; color: white")

        # Initialize
        self.setupUI()
        self.setupSlotHandlers()


class CalibrationWidget(QMainWindow):
    """Full-screen window with calibration steps."""

    completed = QtCore.Signal()
    cancelled = QtCore.Signal()
    shouldCaptureFrame = QtCore.Signal()

    @QtCore.Slot()
    def cancelCalibration(self):
        self.cancelled.emit()

    @QtCore.Slot()
    def beginCalibration(self):
        # Draw circles
        self.drawCircles()
        # Activate the first circle
        self.circles[self.activeCircleIndex].toggleActive()

    def getCircleLocations(self):
        # Get the screen geometry
        screenGeometry = QApplication.primaryScreen().geometry()
        # Get the locations
        locs = []
        trueLeft = 0
        trueMidX = screenGeometry.center().x() - CalibrationCircle.size / 2
        trueMidY = screenGeometry.center().y() - CalibrationCircle.size / 2
        trueRight = screenGeometry.right() - CalibrationCircle.size
        trueTop = 0
        trueBottom = (
            screenGeometry.bottom() - CalibrationCircle.size - self.bottomOffset
        )
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
        # Get the circle locations
        locs = self.getCircleLocations()
        # Draw the circles
        for loc in locs:
            circle = CalibrationCircle(circlesWidget, loc)
            self.circles.append(circle)
        # Set as the central widget
        self.setCentralWidget(circlesWidget)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # If calibration has begun and the spacebar was pressed
        if self.activeCircleIndex is not None and event.key() == QtCore.Qt.Key_Space:
            # Check if calibration is complete
            if self.activeCircleIndex >= len(self.circles) - 1:
                self.completed.emit()
                return super().keyPressEvent(event)
            # Store and progress calibration
            self.shouldCaptureFrame.emit()
            self.circles[self.activeCircleIndex].setParent(None)
            self.activeCircleIndex += 1
            self.circles[self.activeCircleIndex].toggleActive()

        return super().keyPressEvent(event)

    def setupUI(self):
        # pylint: disable=no-member
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
        # Add button container
        buttons = QWidget()
        layout.addWidget(buttons)
        buttonsLayout = QHBoxLayout()
        buttons.setLayout(buttonsLayout)
        # Add cancel button to widget
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancelCalibration)
        buttonsLayout.addWidget(cancelButton)
        # Add begin button to widget
        beginButton = QPushButton("Begin Calibration")
        beginButton.clicked.connect(self.beginCalibration)
        buttonsLayout.addWidget(beginButton)
        # Position the widget
        instructionsWidget.setParent(container)
        (centerX, centerY) = (
            QApplication.primaryScreen().availableGeometry().center().toTuple()
        )
        (widgetWidth, widgetHeight) = instructionsWidget.size().toTuple()
        instructionsWidget.move(
            centerX - widgetWidth, centerY - widgetHeight - self.bottomOffset
        )
        # Set as the central widget
        self.setCentralWidget(container)

    def __init__(self):
        super().__init__()

        # Properties
        self.bottomOffset = 0
        # Adjust for mac OS offset
        if sys.platform == "darwin":
            self.bottomOffset = 35

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Set up attributes
        self.activeCircleIndex: int = 0
        self.circles: list[CalibrationCircle] = []

        self.setupUI()


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

    def __init__(self, parent: QWidget, loc: tuple[int]):
        super().__init__("", parent)

        # Set size
        (x, y) = loc
        self.setGeometry(x, y, self.size, self.size)
        # Set style
        self.setStyle()

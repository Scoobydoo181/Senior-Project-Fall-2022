"""A collection of widgets for the UI.

Referenced snippet for combining cv2 with PySide6: https://gist.github.com/bsdnoobz/8464000
"""
from typing import Any, List, Tuple
import os
import pickle
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
from detectEyes import detectEyes, DetectionType

CALIBRATION_FILE_NAME = "calibrationData.pickle"


class MainWidget(QMainWindow):
    """Main widget showing the video stream in the corner."""

    @QtCore.Slot()
    def cancelCalibration(self):
        self.closeCalibrationWindow()

    @QtCore.Slot()
    def openCalibrationWindow(self):
        self.calibrationWindow = CalibrationWidget()
        self.calibrationWindow.showFullScreen()
        self.calibrationWindow.completed.connect(self.finalizeCalibration)
        self.calibrationWindow.cancelled.connect(self.cancelCalibration)
        self.calibrationWindow.captureEyeData.connect(
            self.captureEyeLocationForCalibration
        )
        self.showMinimized()

    @QtCore.Slot()
    def finalizeCalibration(self):
        # Store calibration data in pickle file
        if os.path.exists(CALIBRATION_FILE_NAME):
            os.remove(CALIBRATION_FILE_NAME)
        with open(CALIBRATION_FILE_NAME, "wb") as handle:
            pickle.dump(self.currentCalibrationData, handle)
        # Clear calibration data
        self.currentCalibrationData = []
        # Close calibration window
        self.closeCalibrationWindow()

    @QtCore.Slot()
    def captureEyeLocationForCalibration(self):
        # Capture eye data
        _, frame = self.capture.read()
        eyes = self.getEyesFromFrame(frame)
        # Store eye data
        self.currentCalibrationData.append(eyes)

    def closeCalibrationWindow(self):
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

    def setupCamera(self):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.previewSize.width())
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.previewSize.height())

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.displayVideoStream)
        self.timer.start(15)

    def drawPupilDetection(self, frame):
        # TODO: move this code into a function/class in detectEyes.py
        eyes = self.getEyesFromFrame(frame)
        for (x, y) in eyes:
            cv2.circle(frame, (x, y), 7, (0, 0, 255), 2)

    def getEyesFromFrame(self, frame):
        # TODO: move this code into a function/class in detectEyes.py
        eyeDetector = cv2.CascadeClassifier("resources/haarcascade_eye.xml")
        detectorParams = cv2.SimpleBlobDetector_Params()
        detectorParams.filterByArea = True
        detectorParams.maxArea = 1500
        blobDetector = cv2.SimpleBlobDetector_create(detectorParams)
        eyes = detectEyes(
            frame,
            DetectionType.EYE_CASCADE_BLOB,
            eyeDetector,
            blobDetector,
        )
        return eyes

    def displayVideoStream(self):
        _, frame = self.capture.read()
        self.drawPupilDetection(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        image = qimage2ndarray.array2qimage(frame)
        self.videoPreview.setPixmap(QtGui.QPixmap.fromImage(image))

    def __init__(self):
        # pylint: disable=no-member
        super().__init__()
        # Properties
        self.previewSize = QtCore.QSize(640, 480)
        self.margin = 40
        self.currentCalibrationData: List[Tuple[int]] = []

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
        self.setupCamera()


class CalibrationWidget(QMainWindow):
    """Full-screen window with calibration steps."""

    completed = QtCore.Signal()
    cancelled = QtCore.Signal()
    captureEyeData = QtCore.Signal()

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
        screenGeometry = QApplication.primaryScreen().availableGeometry()
        # Get the locations
        locs = []
        trueLeft = 0
        trueMidX = screenGeometry.center().x() - CalibrationCircle.size / 2
        trueMidY = screenGeometry.center().y() - CalibrationCircle.size / 2
        trueRight = screenGeometry.right() - CalibrationCircle.size
        trueTop = 0
        # TODO: bottom is different on windows
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
            self.captureEyeData.emit()
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
        instructionsWidget.move(centerX - widgetWidth, centerY - widgetHeight - 35)
        # Set as the central widget
        self.setCentralWidget(container)

    def __init__(self):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Set up attributes
        self.activeCircleIndex: int = 0
        self.circles: List[CalibrationCircle] = []

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

    def __init__(self, parent: QWidget, loc: Tuple[int]):
        super().__init__("", parent)

        # Set size
        (x, y) = loc
        self.setGeometry(x, y, self.size, self.size)
        # Set style
        self.setStyle()

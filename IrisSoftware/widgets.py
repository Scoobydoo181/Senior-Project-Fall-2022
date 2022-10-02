"""A collection of widgets for the UI."""
import math
import sys
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


class DesignTokens:
    """Namespace for tokens used in styling UI components."""

    ### Colors ###
    macOSDarkGray = "#282828"
    macOSDarkerGray = "#1E1E1E"
    blue700 = "#1D4ED8"
    zinc700 = "#3F3F46"
    zinc500 = "#71717A"
    zinc50 = "#F9FAFB"
    ### ###

    ### Component Tokens ###
    # Button
    buttonBaseBgColor = zinc700
    buttonPrimaryBgColor = blue700
    buttonBaseBorderRadius = "5px"
    buttonBaseBorderColor = zinc500
    buttonPrimaryBorderColor = blue700
    buttonBaseBorderWidth = "1px"
    buttonBaseBorderStyle = "solid"
    buttonBasePadding = "10px 20px"
    buttonBaseFontSize = "13px"
    # Circle
    circleBaseBgColor = zinc700
    circleActiveBgColor = blue700
    circleBaseSize = 80
    # Window
    windowBgColor = macOSDarkGray
    windowTextColor = zinc50
    ### ###


class Window(QMainWindow):
    """Styled window."""

    def __setStyle(self):
        self.setStyleSheet(
            f"""
            background-color: {DesignTokens.windowBgColor};
            color: {DesignTokens.windowTextColor};
            """
        )

    def __init__(self):
        super().__init__()

        self.__setStyle()


class MainWindow(Window):
    """Main widget showing the video stream in the corner."""

    TARGET_PREVIEW_HEIGHT = 480

    cameraFrameSignal = QtCore.Signal(ndarray)
    openCalibrationSignal = QtCore.Signal()

    @QtCore.Slot(ndarray)
    def displayCameraFrame(self, frame):
        """This function references the following snippet: https://gist.github.com/bsdnoobz/8464000"""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (self.previewSize.width(), self.previewSize.height()))
        image = qimage2ndarray.array2qimage(frame)
        self.videoPreview.setPixmap(QtGui.QPixmap.fromImage(image))

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
        self.calibrateButton = Button("Calibrate")
        # Connect onClick
        self.calibrateButton.clicked.connect(self.openCalibrationSignal.emit)

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
        self.cameraFrameSignal.connect(self.displayCameraFrame)

    def calculatePreviewSize(self, cameraResolution: tuple[int]) -> QtCore.QSize:
        factor = MainWindow.TARGET_PREVIEW_HEIGHT / float(cameraResolution[1])

        width = math.ceil(cameraResolution[0] * factor)

        print(f"Preview resolution: {width}x{MainWindow.TARGET_PREVIEW_HEIGHT}")

        return QtCore.QSize(width, MainWindow.TARGET_PREVIEW_HEIGHT)

    def __init__(self, cameraResolution: tuple[int]):
        # pylint: disable=no-member
        super().__init__()
        # Properties
        self.previewSize = self.calculatePreviewSize(cameraResolution)
        self.margin = 40
        self.currentCalibrationFrames = []

        # Initialize UI elements
        self.calibrationWindow: CalibrationWindow = None
        self.videoPreview: QLabel = None
        self.calibrateButton: Button = None
        # Initialize camera elements
        self.capture: any = None

        # Remove window title
        self.setWindowTitle("Iris Software")
        # Set window always on top
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # Initialize
        self.setupUI()
        self.setupSlotHandlers()


class CalibrationWindow(Window):
    """Full-screen window with calibration steps."""

    completeSignal = QtCore.Signal()
    cancelSignal = QtCore.Signal()
    captureFrameSignal = QtCore.Signal()

    @QtCore.Slot()
    def cancelCalibration(self):
        self.cancelSignal.emit()

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
        trueMidX = screenGeometry.center().x() - DesignTokens.circleBaseSize / 2
        trueMidY = screenGeometry.center().y() - DesignTokens.circleBaseSize / 2
        trueRight = screenGeometry.right() - DesignTokens.circleBaseSize
        trueTop = 0
        trueBottom = (
            screenGeometry.bottom() - DesignTokens.circleBaseSize - self.bottomOffset
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
            # Capture calibration frame
            self.captureFrameSignal.emit()
            # Check if calibration is complete
            if self.activeCircleIndex >= len(self.circles) - 1:
                self.completeSignal.emit()
            # Otherwise, continue through calibration
            else:
                self.circles[self.activeCircleIndex].setParent(None)
                self.activeCircleIndex += 1
                self.circles[self.activeCircleIndex].toggleActive()
        elif event.key() == QtCore.Qt.Key_Escape:
            # Exit on esc press
            self.cancelSignal.emit()

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
        cancelButton = Button("Cancel")
        cancelButton.clicked.connect(self.cancelCalibration)
        buttonsLayout.addWidget(cancelButton)
        # Add begin button to widget
        beginButton = Button("Begin Calibration", variant="primary")
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

    def toggleActive(self):
        self.active = not self.active
        self.setStyle()

    def setStyle(self):
        bgColor = (
            DesignTokens.circleActiveBgColor
            if self.active
            else DesignTokens.circleBaseBgColor
        )
        borderRadius = f"{DesignTokens.circleBaseSize / 2}px"

        self.setStyleSheet(
            f"""
            background-color: {bgColor};
            border-radius: {borderRadius};
            """
        )

    def __init__(self, parent: QWidget, loc: tuple[int]):
        super().__init__("", parent)

        # Set geometry
        (x, y) = loc
        self.setGeometry(x, y, DesignTokens.circleBaseSize, DesignTokens.circleBaseSize)
        # Set style
        self.setStyle()


class Button(QPushButton):
    """Styled button."""

    def __setStyle(self, variant: str):
        bgColor = (
            DesignTokens.buttonPrimaryBgColor
            if variant == "primary"
            else DesignTokens.buttonBaseBgColor
        )
        borderColor = (
            DesignTokens.buttonPrimaryBorderColor
            if variant == "primary"
            else DesignTokens.buttonBaseBorderColor
        )

        self.setStyleSheet(
            f"""
            background-color: {bgColor};
            border-radius: {DesignTokens.buttonBaseBorderRadius};
            border-width: {DesignTokens.buttonBaseBorderWidth};
            border-color: {borderColor};
            border-style: {DesignTokens.buttonBaseBorderStyle};
            padding: {DesignTokens.buttonBasePadding};
            font-size: {DesignTokens.buttonBaseFontSize};"""
        )

    def __init__(self, label: str, variant: str = "base"):
        super().__init__(label)

        self.__setStyle(variant)

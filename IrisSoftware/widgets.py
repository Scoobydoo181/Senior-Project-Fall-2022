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
    QSizePolicy,
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

    ### Text & Font ###
    fontFamilies = "Inter"
    fontSizeBase = "16px"
    fontSizeLg = "18px"
    fontSizeXl = "20px"
    fontSize2Xl = "24px"
    fontSize4Xl = "36px"
    ### ###

    maxWidthProse = 520

    ### Component Tokens ###
    # Button
    buttonBaseBgColor = zinc700
    buttonPrimaryBgColor = blue700
    buttonBaseBorderRadius = "5px"
    buttonBaseBorderColor = zinc500
    buttonPrimaryBorderColor = blue700
    buttonBaseBorderWidth = "1px"
    buttonBaseBorderStyle = "solid"
    buttonBasePadding = "6px 24px"
    buttonBaseFontWeight = 500
    # Circle
    circleBaseBgColor = zinc700
    circleActiveBgColor = blue700
    circleBaseSize = 80
    # Window
    windowBgColor = macOSDarkGray
    windowTextColor = zinc50
    windowFontSize = fontSizeBase
    windowFontFamily = fontFamilies
    ### ###


class Window(QMainWindow):
    """Styled window."""

    def __setStyle(self):
        self.setStyleSheet(
            f"""
            background-color: {DesignTokens.windowBgColor};
            color: {DesignTokens.windowTextColor};
            font-size: {DesignTokens.windowFontSize};
            font-family: {DesignTokens.windowFontFamily};
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
    def __displayCameraFrame(self, frame):
        """This function references the following snippet: https://gist.github.com/bsdnoobz/8464000"""
        # pylint: disable=no-member
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

    def __calculatePreviewSize(self, cameraResolution: tuple[int]) -> QtCore.QSize:
        factor = MainWindow.TARGET_PREVIEW_HEIGHT / float(cameraResolution[1])
        width = math.ceil(cameraResolution[0] * factor)

        print(f"Preview resolution: {width}x{MainWindow.TARGET_PREVIEW_HEIGHT}")

        return QtCore.QSize(width, MainWindow.TARGET_PREVIEW_HEIGHT)

    def __setupSlotHandlers(self):
        self.cameraFrameSignal.connect(self.__displayCameraFrame)

    def __setupUI(self):
        # Create main window
        centralWidget = QWidget()
        # Create layout container
        layout = QVBoxLayout(centralWidget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create video preview
        self.videoPreview = QLabel()
        self.videoPreview.setFixedSize(self.previewSize)
        layout.addWidget(self.videoPreview)
        # Create calibrate button
        buttonContainer = QWidget()
        buttonContainerLayout = QHBoxLayout(buttonContainer)
        self.calibrateButton = Button("Calibrate")
        self.calibrateButton.clicked.connect(self.openCalibrationSignal.emit)
        buttonContainerLayout.addWidget(self.calibrateButton)
        layout.addWidget(buttonContainer, alignment=QtCore.Qt.AlignCenter)

        # Set the main window
        self.setCentralWidget(centralWidget)
        # Set the position and size of the main window
        self.positionInTopRightCorner()

    def __init__(self, cameraResolution: tuple[int]):
        super().__init__()
        # Properties
        self.previewSize = self.__calculatePreviewSize(cameraResolution)
        self.margin = 40

        # Initialize UI elements
        self.videoPreview: QLabel = None
        self.calibrateButton: Button = None

        # Remove window title
        self.setWindowTitle("Iris Software")
        # Set window always on top
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)

        # Initialize
        self.__setupUI()
        self.__setupSlotHandlers()


class CalibrationWindow(Window):
    """Full-screen window with calibration steps."""

    completeSignal = QtCore.Signal()
    cancelSignal = QtCore.Signal()
    captureFrameSignal = QtCore.Signal()

    @QtCore.Slot()
    def __cancelCalibration(self):
        self.cancelSignal.emit()

    @QtCore.Slot()
    def __beginCalibration(self):
        # Draw circles
        self.__drawCircles()
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

    def __drawCircles(self):
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

    def __setupUI(self):
        # pylint: disable=no-member
        # Create widget
        centralWidget = QWidget()
        centralLayout = QVBoxLayout(centralWidget)
        centralLayout.setAlignment(QtCore.Qt.AlignCenter)
        instructionsWidget = QWidget()
        centralLayout.addWidget(instructionsWidget)
        # Create layout container
        layout = QVBoxLayout(instructionsWidget)
        layout.setSpacing(40)
        # Add title to layout
        title = QLabel("Calibration", alignment=QtCore.Qt.AlignCenter)
        title.setStyleSheet(f"font-size: {DesignTokens.fontSize4Xl};")
        layout.addWidget(title)
        # Add instructions to layout
        instructions = QLabel(
            "Welcome to the calibration process for Iris Software! When you click “Begin”, you will see a series of circles on the screen, with one of them highlighted.\n\nTo progress through calibration, you will need to look at the highlighted circle and then press the spacebar key while looking at the circle.\n\nRepeat this for each circle and then you will be done!",
            alignment=QtCore.Qt.AlignTop,
        )
        instructions.setMaximumWidth(DesignTokens.maxWidthProse)
        instructions.setWordWrap(True)
        layout.addWidget(instructions, alignment=QtCore.Qt.AlignCenter)
        # Add button container
        buttonContainer = QWidget()
        buttonContainer.setStyleSheet("margin-top: 40px;")
        layout.addWidget(buttonContainer, alignment=QtCore.Qt.AlignCenter)
        buttonContainerLayout = QHBoxLayout(buttonContainer)
        # Add cancel button to widget
        cancelButton = Button("Cancel")
        cancelButton.clicked.connect(self.__cancelCalibration)
        buttonContainerLayout.addWidget(cancelButton)
        # Add begin button to widget
        beginButton = Button("Begin", variant="primary")
        beginButton.clicked.connect(self.__beginCalibration)
        buttonContainerLayout.addWidget(beginButton)
        # Set as the central widget
        self.setCentralWidget(centralWidget)

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

        self.__setupUI()


class CalibrationCircle(QPushButton):
    """Circle with an active state and onClick handler."""

    active = False

    def toggleActive(self):
        self.active = not self.active
        self.__setStyle()

    def __setStyle(self):
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
        self.__setStyle()


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
            font-weight: {DesignTokens.buttonBaseFontWeight};
            """
        )

    def __init__(self, label: str, parent: QWidget = None, variant: str = "base"):
        super().__init__(text=label, parent=parent)

        self.__setStyle(variant)

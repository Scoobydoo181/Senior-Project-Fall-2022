"""A collection of widgets for the UI."""
import math
import sys
from enum import Enum
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QApplication,
    QHBoxLayout,
    QSlider,
)
import cv2
import qimage2ndarray
from numpy import ndarray
from settings import loadSettings, PupilModelOptions


class DesignTokens:
    """Namespace for tokens used in styling UI components."""

    ### Colors ###
    macOSDarkGray = "#282828"
    macOSDarkerGray = "#1E1E1E"
    blue700 = "#1D4ED8"
    zinc700 = "#3F3F46"
    zinc600 = "#52525b"
    zinc500 = "#71717A"
    zinc400 = "#a1a1aa"
    zinc300 = "#d4d4d8"
    zinc200 = "#e4e4e7"
    zinc50 = "#F9FAFB"
    ### ###

    ### Text & Font ###
    fontFamilies = "Inter"
    fontSizeBase = "16px"
    fontSizeLg = "18px"
    fontSizeXl = "20px"
    fontSize2Xl = "24px"
    fontSize4Xl = "36px"
    textColorBase = zinc50
    textColorLight = zinc400
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
    # Slider
    sliderGrooveBgColor = zinc700
    sliderGrooveHeight = "8px"
    sliderGrooveBorderRadius = "4px"
    sliderHandleBgColor = blue700
    sliderHandleSize = "16px"
    sliderHandleBorderRadius = "8px"
    sliderHandleMargin = "-4px 0"
    # Circle
    circleBaseBgColor = zinc700
    circleActiveBgColor = blue700
    circleBaseSize = 80
    # Window
    windowBgColor = macOSDarkGray
    windowTextColor = textColorBase
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

    TARGET_PREVIEW_HEIGHT = 240

    cameraFrameSignal = QtCore.Signal(ndarray)
    openMenuSignal = QtCore.Signal()

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
            QApplication.primaryScreen().availableGeometry().right() - self.width(),
            QApplication.primaryScreen().availableGeometry().top(),
        )

    def __calculatePreviewSize(self, cameraResolution: tuple[int]) -> QtCore.QSize:
        factor = MainWindow.TARGET_PREVIEW_HEIGHT / float(cameraResolution[1])
        width = math.ceil(cameraResolution[0] * factor)

        print(f"Preview resolution: {width}x{MainWindow.TARGET_PREVIEW_HEIGHT}")

        return QtCore.QSize(width, MainWindow.TARGET_PREVIEW_HEIGHT)

    def __setupSlotHandlers(self):
        self.cameraFrameSignal.connect(self.__displayCameraFrame)

    def __setupUI(self):
        self.videoPreview = QLabel()
        self.setFixedSize(self.previewSize)

        vLayout = QVBoxLayout(self.videoPreview)
        hLayout = QHBoxLayout()

        self.menuButton = Button("Menu")
        self.menuButton.clicked.connect(self.openMenuSignal.emit)

        hLayout.addStretch()
        hLayout.addWidget(self.menuButton)
        vLayout.addLayout(hLayout)
        vLayout.addStretch()

        self.setCentralWidget(self.videoPreview)
        self.positionInTopRightCorner()

    def __init__(self, cameraResolution: tuple[int, int]):
        super().__init__()
        # Properties
        self.previewSize = self.__calculatePreviewSize(cameraResolution)

        # Initialize UI elements
        self.videoPreview: QLabel = None
        self.calibrateButton: Button = None
        self.menuButton: Button = None

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
    captureEyeCoordsSignal = QtCore.Signal()

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
            # Capture calibration eye coords
            self.captureEyeCoordsSignal.emit()
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

    def changeVariant(self, variant: str):
        self.variant = variant
        self.__setStyle()

    def __setStyle(self):
        bgColor = (
            DesignTokens.buttonPrimaryBgColor
            if self.variant == "primary"
            else DesignTokens.buttonBaseBgColor
        )
        borderColor = (
            DesignTokens.buttonPrimaryBorderColor
            if self.variant == "primary"
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

        self.variant = variant

        self.__setStyle()


class ProseText(QLabel):
    """Text with a constrained width."""

    def __setStyle(self):
        textColor = (
            DesignTokens.textColorLight if self.light else DesignTokens.textColorBase
        )

        self.setStyleSheet(
            f"""
            color: {textColor};
            max-width: {DesignTokens.maxWidthProse};
            """
        )

        self.setWordWrap(True)
        self.setMinimumWidth(DesignTokens.maxWidthProse)

    def __init__(self, text: str, light: bool = False):
        super().__init__(text)

        self.light = light

        self.__setStyle()


class Slider(QSlider):
    """
    Styled slider.

    For styling tips, see https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qslider.
    """

    def __setStyle(self):
        self.setStyleSheet(
            f"""
            QSlider::groove {{
                background-color: {DesignTokens.sliderGrooveBgColor};
                height: {DesignTokens.sliderGrooveHeight};
                border-radius: {DesignTokens.sliderGrooveBorderRadius};
            }}
            QSlider::handle {{
                background-color: {DesignTokens.sliderHandleBgColor};
                height: {DesignTokens.sliderHandleSize};
                width: {DesignTokens.sliderHandleSize};
                border-radius: {DesignTokens.sliderHandleBorderRadius};
                margin: {DesignTokens.sliderHandleMargin};
            }}
            """
        )

    def __init__(
        self,
        low: int,
        high: int,
        initialValue: int = None,
        orientation: QtCore.Qt.Orientation = QtCore.Qt.Orientation.Horizontal,
    ):
        super().__init__(orientation)

        self.setMinimum(low)
        self.setMaximum(high)
        if initialValue:
            self.setValue(initialValue)

        self.__setStyle()


class SelectionGroup(QWidget):
    """Group of buttons for selecting an option."""

    class SelectionOption:
        """Helper type for SelectionGroup."""

        def __init__(self, label: str, callback: callable) -> None:
            self.label = label
            self.callback = callback

    def __init__(self, options: list[SelectionOption], initialSelection: int = 0):
        super().__init__()

        self.initialSelection = initialSelection
        self.options = options
        self.buttons: list[Button] = []
        self.mapping: dict[str, int] = {}

        self.__setupUI()

    def updateSelection(self, label: str):
        target = self.mapping[label]

        for i, v in enumerate(self.buttons):
            if i == target:
                v.changeVariant("primary")
            else:
                v.changeVariant("base")

    def __setupUI(self):
        layout = QHBoxLayout(self)

        for i, opt in enumerate(self.options):
            button = Button(opt.label)
            if i == self.initialSelection:
                button.changeVariant("primary")
            button.clicked.connect(opt.callback)
            self.mapping[opt.label] = i
            self.buttons.append(button)
            layout.addWidget(button)

        layout.addStretch()


class MenuWindow(Window):
    """Menu for settings of the program."""

    openCalibrationSignal = QtCore.Signal()
    changePupilModelSignal = QtCore.Signal(PupilModelOptions)
    changeEyeColorThresholdSignal = QtCore.Signal(int)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Iris Software - Menu")

        self.savedSettings = loadSettings()

        self.calibrationButtonContainer: QWidget

        self.eyeColorThresholdContainer: QWidget

        self.pupilModelMapping = {
            PupilModelOptions.ACCURACY: "Accuracy",
            PupilModelOptions.SPEED: "Speed",
        }
        self.pupilModelSelectionGroup: SelectionGroup

        self.__setupUI()

    def __modelChangeCallback(self, value: PupilModelOptions):
        self.changePupilModelSignal.emit(value)
        self.pupilModelSelectionGroup.updateSelection(self.pupilModelMapping[value])

    def __modelChangeAccuracyCallback(self):
        self.__modelChangeCallback(PupilModelOptions.ACCURACY)

    def __modelChangeSpeedCallback(self):
        self.__modelChangeCallback(PupilModelOptions.SPEED)

    def __setupPupilModelSelectionGroup(self):
        pupilModelSelectionOptions = [
            SelectionGroup.SelectionOption(
                self.pupilModelMapping[PupilModelOptions.ACCURACY],
                self.__modelChangeAccuracyCallback,
            ),
            SelectionGroup.SelectionOption(
                self.pupilModelMapping[PupilModelOptions.SPEED],
                self.__modelChangeSpeedCallback,
            ),
        ]

        defaultValue = 0
        if self.savedSettings.pupilDetectionModel is PupilModelOptions.SPEED:
            defaultValue = 1

        self.pupilModelSelectionGroup = SelectionGroup(
            pupilModelSelectionOptions, defaultValue
        )

    def __setupEyeColorThresholdSlider(self):
        self.eyeColorThresholdContainer = QWidget()
        layout = QHBoxLayout(self.eyeColorThresholdContainer)

        eyeColorThresholdSlider = Slider(1, 10, self.savedSettings.eyeColorThreshold)
        eyeColorThresholdSlider.valueChanged.connect(
            self.changeEyeColorThresholdSignal.emit
        )

        layout.addWidget(eyeColorThresholdSlider)
        layout.addStretch()

    def __setupCalibrationButton(self):
        self.calibrationButtonContainer = QWidget()
        layout = QHBoxLayout(self.calibrationButtonContainer)

        calibrationButton = Button("Calibrate")
        calibrationButton.clicked.connect(self.openCalibrationSignal.emit)

        layout.addWidget(calibrationButton)
        layout.addStretch()

    def __setupUI(self):
        centralWidget = QWidget()
        centerLayout = QHBoxLayout(centralWidget)
        centerLayout.addStretch()
        layout = QVBoxLayout()
        centerLayout.addLayout(layout)
        centerLayout.addStretch()

        modelPrioritizationLabel = ProseText("Model Prioritization")
        eyeColorThresholdLabel = ProseText("Eye Color Threshold")
        eyeColorThresholdDesc = ProseText(
            "Adjust this if the program is not properly detecting your pupils. A higher value will work better for light colored eyes.",
            True,
        )
        calibrationLabel = ProseText("Calibration")

        self.__setupCalibrationButton()
        self.__setupPupilModelSelectionGroup()
        self.__setupEyeColorThresholdSlider()

        layout.addStretch()
        layout.addWidget(modelPrioritizationLabel)
        layout.addWidget(self.pupilModelSelectionGroup)
        layout.addWidget(eyeColorThresholdLabel)
        layout.addWidget(eyeColorThresholdDesc)
        layout.addWidget(self.eyeColorThresholdContainer)
        layout.addWidget(calibrationLabel)
        layout.addWidget(self.calibrationButtonContainer)
        layout.addStretch()

        self.setCentralWidget(centralWidget)

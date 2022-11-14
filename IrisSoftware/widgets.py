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
    QSlider,
)
import cv2
import qimage2ndarray
from numpy import ndarray
from settings import loadSettings, PupilModelOptions

MODIFIER_KEY = "CMD" if sys.platform == "darwin" else "CTRL"


def checkCloseKeyCombo(event: QtGui.QKeyEvent):
    return event.keyCombination() == QtCore.QKeyCombination.fromCombined(
        QtCore.Qt.CTRL | QtCore.Qt.Key_W
    )


def checkMenuKeyCombo(event: QtGui.QKeyEvent):
    return event.keyCombination() == QtCore.QKeyCombination.fromCombined(
        QtCore.Qt.CTRL | QtCore.Qt.Key_1
    )


def checkCancelKey(event: QtGui.QKeyEvent):
    return event.key() == QtCore.Qt.Key_Escape


def checkContinueKey(event: QtGui.QKeyEvent):
    return event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return


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


class InstructionsWindow(Window):
    """Window for displaying instructions."""

    closeSignal = QtCore.Signal()
    continueSignal = QtCore.Signal()

    def closeEvent(self, _) -> None:
        self.closeSignal.emit()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if checkCancelKey(event) or checkCloseKeyCombo(event):
            self.closeSignal.emit()
        elif checkContinueKey(event):
            self.continueSignal.emit()
        else:
            # Handle normal key presses
            return super().keyPressEvent(event)

    def __init__(self):
        super().__init__()

        self.continueButton: Button
        self.closeButton: Button

        self.__setupUI()

    def __setupUI(self):
        widget = QWidget()
        horizontalLayout = QHBoxLayout(widget)
        verticalLayout = QVBoxLayout()

        horizontalLayout.addStretch()
        horizontalLayout.addLayout(verticalLayout)
        horizontalLayout.addStretch()
        horizontalLayout.setContentsMargins(40, 40, 40, 40)

        buttonLayout = QHBoxLayout()
        self.continueButton = Button("Continue [ENTER]", variant="primary")
        self.continueButton.clicked.connect(self.continueSignal.emit)
        self.closeButton = Button("Close [ESC]")
        self.closeButton.clicked.connect(self.closeSignal.emit)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.closeButton)
        buttonLayout.addSpacing(20)
        buttonLayout.addWidget(self.continueButton)
        buttonLayout.addStretch()

        title = Heading("Iris Software - Welcome")
        instructions = ProseText(
            f"Welcome to Iris Software - a program that allows you to control your computer with your eyes. Before being able to use the program, you'll go through a calibration process.\n\nAfter this calibration progress, the program will start. To move the mouse, move your eyes either up, down, left, or right of the boxes drawn around them to move in that direction. Return your eyes to the center of the boxes to stop moving the mouse.\n\nTo perform a mouse click, simply perform an exaggerated blink with your eyes.\n\nIf at any time you would like to close a window, use the key combination [{MODIFIER_KEY}] + [W]. Closing all windows will exit the program.",
            True,
        )

        verticalLayout.addStretch()
        verticalLayout.addWidget(title, alignment=QtCore.Qt.AlignHCenter)
        verticalLayout.addSpacing(40)
        verticalLayout.addWidget(instructions)
        verticalLayout.addSpacing(40)
        verticalLayout.addLayout(buttonLayout)
        verticalLayout.addStretch()

        self.setCentralWidget(widget)


class MainWindow(Window):
    """Main widget showing the video stream in the corner."""

    TARGET_PREVIEW_HEIGHT = 480

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

        self.menuButton = Button(f"Menu [{MODIFIER_KEY}] + [1]")
        self.menuButton.clicked.connect(self.openMenuSignal.emit)
        self.closeButton = Button(f"Close [{MODIFIER_KEY}] + [W]")
        self.closeButton.clicked.connect(self.close)

        hLayout.addWidget(self.closeButton)
        hLayout.addStretch()
        hLayout.addWidget(self.menuButton)
        vLayout.addLayout(hLayout)
        vLayout.addStretch()

        self.setCentralWidget(self.videoPreview)
        self.positionInTopRightCorner()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if checkMenuKeyCombo(event):
            self.openMenuSignal.emit()
        elif checkCloseKeyCombo(event):
            self.close()
        else:
            # Handle normal key presses
            return super().keyPressEvent(event)

    def __init__(self, cameraResolution: tuple[int, int]):
        super().__init__()
        # Properties
        self.previewSize = self.__calculatePreviewSize(cameraResolution)

        # Initialize UI elements
        self.videoPreview: QLabel = None
        self.calibrateButton: Button = None
        self.menuButton: Button = None
        self.closeButton: Button = None

        # Remove window title
        self.setWindowTitle("Iris Software")

        # Initialize
        self.__setupUI()
        self.__setupSlotHandlers()


class CalibrationWindow(Window):
    """Full-screen window with calibration steps."""

    completeSignal = QtCore.Signal()
    cancelSignal = QtCore.Signal()
    captureEyeCoordsSignal = QtCore.Signal()
    finishedCaptureEyeCoordsSignal = QtCore.Signal()

    @QtCore.Slot()
    def __cancelCalibration(self):
        self.cancelSignal.emit()

    @QtCore.Slot()
    def __beginCalibration(self):
        # Draw circles
        self.__drawCircles()
        # Activate the first circle
        self.circles[self.activeCircleIndex].toggleActive()

    @QtCore.Slot()
    def __progressCalibration(self):
        self.circles[self.activeCircleIndex].setHidden()
        # Check if calibration is complete
        if self.activeCircleIndex >= len(self.circles) - 1:
            self.completeSignal.emit()
        # Otherwise, continue through calibration
        else:
            self.activeCircleIndex += 1
            self.circles[self.activeCircleIndex].toggleActive()

    def getCircleLocations(self):
        locs = []

        for c in self.circles:
            locs.append(c.getPositionOnScreen())

        return locs

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # If calibration has begun and the spacebar was pressed
        if len(self.circles) == 0 and checkContinueKey(event):
            self.__beginCalibration()
        if self.activeCircleIndex is not None and event.key() == QtCore.Qt.Key_Space:
            self.captureEyeCoordsSignal.emit()
        elif checkCancelKey(event) or checkCloseKeyCombo(event):
            self.cancelSignal.emit()
        else:
            # Handle other key presses
            return super().keyPressEvent(event)

    def __drawCircles(self):
        gridSize = 5
        circlesWidget = QWidget()
        verticalLayout = QVBoxLayout(circlesWidget)
        verticalLayout.setContentsMargins(0, 0, 0, 0)

        for i in range(gridSize):
            # Create the horizontal layout
            horizontalLayout = QHBoxLayout()
            horizontalLayout.setContentsMargins(0, 0, 0, 0)
            verticalLayout.addLayout(horizontalLayout)
            if i < gridSize - 1:
                verticalLayout.addStretch()

            # Draw the circles
            for j in range(gridSize):
                circle = CalibrationCircle()
                horizontalLayout.addWidget(circle)
                self.circles.append(circle)
                if j < gridSize - 1:
                    horizontalLayout.addStretch()

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
        title = Heading("Calibration")
        layout.addWidget(title, alignment=QtCore.Qt.AlignHCenter)
        # Add instructions to layout
        instructions = QLabel(
            "Welcome to the calibration process for Iris Software! When you click “Begin”, you will see a series of circles on the screen, with one of them highlighted.\n\nTo progress through calibration, you will need to look at the highlighted circle and then press the [SPACE] key while looking at the circle.\n\nRepeat this for each circle and then you will be done!",
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
        cancelButton = Button("Cancel [ESC]")
        cancelButton.clicked.connect(self.__cancelCalibration)
        buttonContainerLayout.addWidget(cancelButton)
        # Add begin button to widget
        beginButton = Button("Begin [ENTER]", variant="primary")
        beginButton.clicked.connect(self.__beginCalibration)
        buttonContainerLayout.addWidget(beginButton)
        # Set as the central widget
        self.setCentralWidget(centralWidget)

    def __init__(self):
        super().__init__()

        # Remove window title
        self.setWindowTitle("Iris Software - Calibration")

        # Set up attributes
        self.activeCircleIndex: int = 0
        self.circles: list[CalibrationCircle] = []

        self.finishedCaptureEyeCoordsSignal.connect(self.__progressCalibration)

        self.__setupUI()


class CalibrationCircle(QPushButton):
    """Circle with an active state and onClick handler."""

    def getPositionOnScreen(self) -> tuple[int, int]:
        """Return the screen coordinates of the center of the circle."""
        centerOfCircle = QtCore.QPoint(
            DesignTokens.circleBaseSize / 2, DesignTokens.circleBaseSize / 2
        )
        posOnScreen = self.mapToGlobal(centerOfCircle)
        return posOnScreen.toTuple()

    def toggleActive(self):
        self.active = not self.active
        self.__setStyle()

    def setHidden(self):
        self.setStyleSheet(
            f"""
            background-color: {DesignTokens.windowBgColor};
            border: none;
            """
        )

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
            border: none;
            """
        )

    def __init__(self):
        super().__init__("")

        self.active = False

        self.setFixedSize(DesignTokens.circleBaseSize, DesignTokens.circleBaseSize)
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


class Heading(QLabel):
    """Text as a heading."""

    def __setStyle(self):
        self.setStyleSheet(
            f"""
            font-size: {DesignTokens.fontSize4Xl};
            """
        )

    def __init__(self, text: str):
        super().__init__(text)

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


EYE_COLOR_THRESHOLD_RANGE = (0, 20)


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
        self.eyeColorThresholdValueLabel: QLabel

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

    def __eyeColorThresholdValueChange(self, value: int):
        self.changeEyeColorThresholdSignal.emit(value)
        self.eyeColorThresholdValueLabel.setText(f"Value: {value}")

    def __setupEyeColorThresholdSlider(self):
        self.eyeColorThresholdContainer = QWidget()
        verticalLayout = QVBoxLayout(self.eyeColorThresholdContainer)
        horizontalLayout = QHBoxLayout()

        self.eyeColorThresholdValueLabel = QLabel(
            f"Value: {self.savedSettings.eyeColorThreshold}"
        )

        eyeColorThresholdSlider = Slider(
            EYE_COLOR_THRESHOLD_RANGE[0],
            EYE_COLOR_THRESHOLD_RANGE[1],
            self.savedSettings.eyeColorThreshold,
        )
        eyeColorThresholdSlider.valueChanged.connect(
            self.__eyeColorThresholdValueChange
        )

        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addWidget(
            self.eyeColorThresholdValueLabel, alignment=QtCore.Qt.AlignHCenter
        )

        horizontalLayout.addWidget(QLabel("Dark Eyes"))
        horizontalLayout.addWidget(eyeColorThresholdSlider)
        horizontalLayout.addWidget(QLabel("Light Eyes"))

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
            "If the program is not detecting your eyes, please try adjusting this value visually until your eyes are detected.",
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

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if checkCloseKeyCombo(event):
            self.close()
        else:
            # Handle normal key presses
            return super().keyPressEvent(event)

"""Handles running the UI elements."""
import sys
import pathlib
from PySide6.QtWidgets import QApplication
from widgets import (
    MainWindow,
    CalibrationWindow,
    InstructionsWindow,
    MenuWindow,
    PupilModelOptions,
    EYE_COLOR_THRESHOLD_RANGE,
    InitialConfigWindow,
)
from PySide6 import QtCore, QtGui


CALIBRATION_FILE_NAME = "calibrationData.pickle"
INTER_FONT_PATH = str(pathlib.Path("./resources/InterVariableFont.ttf").resolve())


class UI:
    """Responsible for handling the user interface."""

    def __init__(self, cameraResolution: tuple[int, int]) -> None:
        print("Initializing UI...")
        # Create app
        self.app = QApplication([])
        # Load Inter font
        QtGui.QFontDatabase.addApplicationFont(INTER_FONT_PATH)
        self.cameraResolution = cameraResolution
        # Create windows
        self.mainWindow: MainWindow
        self.calibrationWindow: CalibrationWindow
        self.menuWindow: MenuWindow
        self.initialConfigWindow: InitialConfigWindow
        # Create callback properties
        self.onCaptureCalibrationEyeCoords: callable
        self.onCalibrationCancel: callable
        self.onCalibrationComplete: callable
        self.onChangePupilModel: callable
        self.onChangeEyeColorThreshold: callable
        print("UI initialized.")

    def runInitialCalibration(self):
        self.__openCalibration(initial=True)
        print("Initial calibration running.")
        return self.app.exec()

    def runShowInstructions(self):
        instructionsWindow = InstructionsWindow()
        instructionsWindow.continueSignal.connect(self.__handleInstructionsContinue)
        instructionsWindow.closeSignal.connect(self.__handleInstructionsClose)
        instructionsWindow.show()
        print("Show instructions running.")
        return self.app.exec()

    def runInitialConfiguration(self):
        self.initialConfigWindow = InitialConfigWindow(self.cameraResolution)
        self.initialConfigWindow.changeEyeColorThresholdSignal.connect(
            self.onChangeEyeColorThreshold
        )
        self.initialConfigWindow.show()
        print("Initial configuration running.")
        return self.app.exec()

    def run(self):
        self.__createMainWindow()
        self.mainWindow.show()
        print("UI running.")
        return self.app.exec()

    def closeCalibrationWindow(self):
        if hasattr(self, "calibrationWindow") and self.calibrationWindow is not None:
            self.calibrationWindow.close()
            self.calibrationWindow = None

    def closeMenuWindow(self):
        if hasattr(self, "menuWindow") and self.menuWindow is not None:
            self.menuWindow.close()
            self.menuWindow = None

    def closeMainWindow(self):
        if hasattr(self, "mainWindow") and self.mainWindow is not None:
            self.mainWindow.close()
            self.mainWindow = None

    def emitCameraFrame(self, frame):
        if self.initialConfigWindow is not None:
            self.initialConfigWindow.cameraFrameSignal.emit(frame)
        if self.mainWindow is not None:
            self.mainWindow.cameraFrameSignal.emit(frame)

    def emitFinishedCaptureEyeCoords(self):
        self.calibrationWindow.finishedCaptureEyeCoordsSignal.emit()

    def __createMainWindow(self):
        self.mainWindow = MainWindow(self.cameraResolution)
        self.mainWindow.openMenuSignal.connect(self.__handleMenuOpen)

    def __openCalibration(self, initial=False):
        # Create window
        self.calibrationWindow = CalibrationWindow()
        # Connect signal handlers
        if initial:
            self.calibrationWindow.completeSignal.connect(
                self.__handleCalibrationCompleteInitial
            )
            self.calibrationWindow.cancelSignal.connect(
                self.__handleCalibrationCancelInitial
            )

        else:
            self.calibrationWindow.completeSignal.connect(
                self.__handleCalibrationComplete
            )
            self.calibrationWindow.cancelSignal.connect(self.__handleCalibrationCancel)

        self.calibrationWindow.captureEyeCoordsSignal.connect(
            self.__handleCalibrationCaptureEyeCoords
        )
        # Show the window
        self.calibrationWindow.showFullScreen()

    ### Signal handlers ###

    @QtCore.Slot()
    def __handleInstructionsClose(self):
        self.app.exit(-1)

    @QtCore.Slot()
    def __handleInstructionsContinue(self):
        self.app.exit()

    @QtCore.Slot(PupilModelOptions)
    def __handleChangePupilModel(self, value: PupilModelOptions):
        if hasattr(self, "onChangePupilModel"):
            self.onChangePupilModel(value)

    @QtCore.Slot(int)
    def __handleChangeEyeColorThreshold(self, value: int):
        if hasattr(self, "onChangeEyeColorThreshold"):
            self.onChangeEyeColorThreshold(value)

    @QtCore.Slot()
    def __handleMenuOpen(self):
        self.closeMenuWindow()
        self.menuWindow = MenuWindow()
        self.menuWindow.openCalibrationSignal.connect(self.__handleCalibrationOpen)
        self.menuWindow.changePupilModelSignal.connect(self.__handleChangePupilModel)
        self.menuWindow.changeEyeColorThresholdSignal.connect(
            self.__handleChangeEyeColorThreshold
        )
        self.menuWindow.show()

    @QtCore.Slot()
    def __handleCalibrationOpen(self):
        self.closeMenuWindow()
        self.closeMainWindow()
        self.__openCalibration()

    @QtCore.Slot()
    def __handleCalibrationCancelInitial(self):
        self.app.exit(-1)

    @QtCore.Slot()
    def __handleCalibrationCancel(self):
        # Callback
        if hasattr(self, "onCalibrationCancel"):
            self.onCalibrationCancel()
        self.closeCalibrationWindow()
        self.__createMainWindow()
        self.mainWindow.showNormal()

    @QtCore.Slot()
    def __handleCalibrationCompleteInitial(self):
        # Callback
        if hasattr(self, "onCalibrationComplete"):
            self.onCalibrationComplete()
        self.closeCalibrationWindow()
        self.app.exit()

    @QtCore.Slot()
    def __handleCalibrationComplete(self):
        # Callback
        if hasattr(self, "onCalibrationComplete"):
            self.onCalibrationComplete()
        self.closeCalibrationWindow()
        self.__createMainWindow()
        self.mainWindow.showNormal()

    @QtCore.Slot()
    def __handleCalibrationCaptureEyeCoords(self):
        # Callback
        if hasattr(self, "onCaptureCalibrationEyeCoords"):
            self.onCaptureCalibrationEyeCoords()

    ### ###


if __name__ == "__main__":
    ui = UI((640, 480))
    sys.exit(ui.run())

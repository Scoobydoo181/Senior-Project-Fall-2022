from enum import Enum
import os
import pickle

SETTINGS_FILE_NAME = "settings.pickle"


class PupilModelOptions(Enum):
    """Helper enum for pupil models."""

    ACCURACY = 1
    SPEED = 2


class Settings:
    """Wrapper for settings data from UI."""

    def __init__(self) -> None:
        self.pupilDetectionModel = PupilModelOptions.ACCURACY
        self.eyeColorThreshold: int = 1


def loadSettings() -> Settings:
    if os.path.exists(SETTINGS_FILE_NAME):
        with open(SETTINGS_FILE_NAME, "rb") as handle:
            return pickle.load(handle)
    else:
        return Settings()


def saveSettings(data: Settings):
    if os.path.exists(SETTINGS_FILE_NAME):
        os.remove(SETTINGS_FILE_NAME)

    with open(SETTINGS_FILE_NAME, "wb") as handle:
        pickle.dump(data, handle)

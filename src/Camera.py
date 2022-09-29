"""Holds code for the camera device."""
import cv2
from numpy import ndarray


class Camera:
    """Abstraction of the cv2 VideoCapture device."""

    TARGET_RESOLUTION_HEIGHT = 480

    def __init__(self) -> None:
        print("Initializing camera...")
        # Get access to the VideoCapture device
        self.capture = cv2.VideoCapture(0)
        # Calculate an adjusted resolution
        baseWidth = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        baseHeight = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        print(f"Camera resolution: {baseWidth}x{baseHeight}")

        factor = float(Camera.TARGET_RESOLUTION_HEIGHT / baseHeight)

        resolutionWidth = int(baseWidth * factor)

        self.resolution: tuple[int] = (resolutionWidth, Camera.TARGET_RESOLUTION_HEIGHT)

        print(
            f"Adjusted resolution: {resolutionWidth}x{Camera.TARGET_RESOLUTION_HEIGHT}"
        )
        # Adjust the resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

    def getResolution(self) -> tuple[int]:
        return self.resolution

    def getFrame(self) -> ndarray:
        # Capture the current frame from the camera
        _, frame = self.capture.read()

        return frame

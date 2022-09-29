"""Holds code for the camera device."""
import cv2
from numpy import ndarray


class Camera:
    """Abstraction of the cv2 VideoCapture device."""

    COMMON_RESOLUTIONS = [(640, 480), (854, 480), (1280, 720), (1920, 1080)]

    def __init__(self) -> None:
        print("Initializing camera...")
        # Get access to the VideoCapture device
        self.capture = cv2.VideoCapture(0)
        # Get the minimum supported common resolution
        actualW = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actualH = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Actual camera resolution: {actualW}x{actualH}")
        self.resolution: tuple[int] = min(self.getSupportedResolutions())
        print(f"Adjusted camera resolution: {self.resolution[0]}x{self.resolution[1]}")
        # Adjust the resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

    def getSupportedResolutions(self) -> list[tuple[int]]:
        resolutions = []

        for res in Camera.COMMON_RESOLUTIONS:
            # Set the camera frame to that size
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, res[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, res[1])
            # Verify
            actualW = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            actualH = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            if actualW == res[0] and actualH == res[1]:
                resolutions.append(res)

        return resolutions

    def getResolution(self) -> tuple[int]:
        return self.resolution

    def getFrame(self) -> ndarray:
        # Capture the current frame from the camera
        _, frame = self.capture.read()

        return frame

"""Holds code for the camera device."""
import cv2
from numpy import ndarray


class Camera:
    """Abstraction of the cv2 VideoCapture device."""

    def __init__(self) -> None:
        print("Initializing camera...")
        # Get access to the VideoCapture device
        self.capture = cv2.VideoCapture(0)
        # Get the resolution
        width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.resolution = (width, height)
        print("Camera initialized.")

    def getResolution(self) -> tuple[int]:
        return self.resolution

    def getFrame(self) -> ndarray:
        # Capture the current frame from the camera
        _, frame = self.capture.read()

        return frame

    def release(self) -> None:
        self.capture.release()
        print("Camera released.")

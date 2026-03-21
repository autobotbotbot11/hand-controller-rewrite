from __future__ import annotations


class Camera:
    """Small OpenCV camera wrapper with explicit lifecycle control."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        import cv2

        self.index = index
        self.width = width
        self.height = height
        self._cv2 = cv2
        self.cap = cv2.VideoCapture(self.index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self):
        return self.cap.read()

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()

    def is_opened(self) -> bool:
        return bool(self.cap is not None and self.cap.isOpened())

    def __enter__(self) -> "Camera":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

from __future__ import annotations

from contextlib import contextmanager
import sys
from typing import Any


def _backend_candidates(cv2: Any) -> list[int | None]:
    candidates: list[int | None] = [None]
    if sys.platform == "win32":
        for attr in ("CAP_MSMF", "CAP_DSHOW"):
            value = getattr(cv2, attr, None)
            if isinstance(value, int) and value not in candidates:
                candidates.append(value)
    return candidates


def _open_capture(
    cv2: Any,
    *,
    index: int,
    width: int,
    height: int,
) -> tuple[Any | None, int | None]:
    for backend in _backend_candidates(cv2):
        cap = None
        try:
            cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
            if cap is not None and cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                return cap, backend
        except Exception:
            pass
        finally:
            if cap is not None and not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
    return None, None


@contextmanager
def _quiet_cv_logging(cv2: Any):
    get_level = getattr(cv2, "getLogLevel", None)
    set_level = getattr(cv2, "setLogLevel", None)
    if not callable(get_level) or not callable(set_level):
        yield
        return

    previous = None
    try:
        previous = get_level()
        set_level(0)
    except Exception:
        previous = None

    try:
        yield
    finally:
        if previous is not None:
            try:
                set_level(previous)
            except Exception:
                pass


def detect_available_cameras(*, max_index: int = 5, width: int = 640, height: int = 480) -> list[tuple[str, int]]:
    try:
        import cv2
    except ModuleNotFoundError:
        return [("Default Webcam", 0)]

    sources: list[tuple[str, int]] = []
    with _quiet_cv_logging(cv2):
        for index in range(max_index):
            cap, _ = _open_capture(cv2, index=index, width=width, height=height)
            if cap is None:
                continue
            try:
                sources.append(("Default Webcam" if index == 0 else f"Camera {index}", index))
            finally:
                try:
                    cap.release()
                except Exception:
                    pass
    return sources or [("Default Webcam", 0)]


class Camera:
    """Small OpenCV camera wrapper with explicit lifecycle control."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        import cv2

        self.index = index
        self.width = width
        self.height = height
        self._cv2 = cv2
        self.cap, self.backend = _open_capture(
            cv2,
            index=self.index,
            width=self.width,
            height=self.height,
        )

    def read(self):
        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def is_opened(self) -> bool:
        return bool(self.cap is not None and self.cap.isOpened())

    def __enter__(self) -> "Camera":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

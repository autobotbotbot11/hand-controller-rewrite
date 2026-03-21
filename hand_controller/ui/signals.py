from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal


class OverlaySignalBus(QObject):
    update_overlay = pyqtSignal(object)

from __future__ import annotations

from PyQt5.QtCore import QRect, Qt, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

from .payloads import OverlayPayload


class OverlayWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.payload = OverlayPayload()
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Hand Controller Overlay")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.showFullScreen()

    @pyqtSlot(object)
    def apply_payload(self, payload: object) -> None:
        if not isinstance(payload, OverlayPayload):
            return
        self.payload = payload
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self._draw_selfie(painter)
        if self.payload.keyboard_visible:
            self._draw_keyboard(painter)
        self._draw_skeleton(painter)
        self._draw_pointers(painter)
        self._draw_header(painter)
        self._draw_status(painter)
        self._draw_footer(painter)

    def _draw_keyboard(self, painter: QPainter) -> None:
        painter.setFont(QFont("Arial", 14))
        for key in self.payload.keyboard_keys:
            highlighted = key.label in self.payload.highlight_labels
            fill = QColor(0, 0, 0, 155) if not highlighted else QColor(0, 120, 220, 185)
            border = QColor(255, 255, 255, 210) if highlighted else QColor(185, 185, 185, 180)

            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(border, 2 if not highlighted else 3))
            rect = QRect(key.x1, key.y1, key.x2 - key.x1, key.y2 - key.y1)
            painter.drawRect(rect)

            label = "SPC" if key.label == "SPACE" else key.label
            painter.setPen(QColor(255, 255, 255, 230))
            painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_skeleton(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
        for x1, y1, x2, y2 in self.payload.skeleton_lines:
            painter.drawLine(x1, y1, x2, y2)

    def _draw_pointers(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(0, 255, 255, 230), 2))
        painter.setBrush(QBrush(QColor(0, 255, 255, 90)))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        for pointer in self.payload.finger_points:
            painter.drawEllipse(pointer.x - 9, pointer.y - 9, 18, 18)
            if pointer.hand_label:
                painter.setPen(QColor(255, 255, 255, 230))
                painter.drawText(pointer.x + 12, pointer.y - 6, pointer.hand_label)
                painter.setPen(QPen(QColor(0, 255, 255, 230), 2))

    def _draw_header(self, painter: QPainter) -> None:
        painter.setFont(QFont("Arial", 14))
        painter.setPen(QColor(255, 255, 255, 230))
        header = f"mode: {self.payload.mode}    control: {'on' if self.payload.control_enabled else 'off'}"
        if self.payload.profile_label:
            header += f"    profile: {self.payload.profile_label}"
        painter.drawText(20, 34, header)

    def _draw_status(self, painter: QPainter) -> None:
        lines = []
        if self.payload.mode == "mouse" and self.payload.mouse_status:
            lines.append(self.payload.mouse_status)
        if self.payload.mode == "keyboard" and self.payload.keyboard_status:
            lines.append(self.payload.keyboard_status)
        lines.extend(self.payload.debug_tags)

        if not lines:
            return

        x = 20
        y = 64
        width = min(self.width() - 40, 880)
        height = 30 + max(0, len(lines) - 1) * 22
        rect = QRect(x, y, width, height)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.setPen(QPen(QColor(0, 0, 0, 0), 0))
        painter.drawRect(rect)

        painter.setFont(QFont("Arial", 12))
        painter.setPen(QColor(255, 235, 190, 240))
        line_y = y + 20
        for line in lines:
            painter.drawText(x + 10, line_y, line)
            line_y += 22

    def _draw_footer(self, painter: QPainter) -> None:
        if not self.payload.footer_hint:
            return
        painter.setFont(QFont("Arial", 11))
        painter.setPen(QColor(190, 190, 190, 220))
        painter.drawText(20, self.height() - 24, self.payload.footer_hint)

    def _draw_selfie(self, painter: QPainter) -> None:
        frame = self.payload.selfie_frame
        if frame is None:
            return

        try:
            import cv2
        except ModuleNotFoundError:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        target = QRect(20, 110, w, h)
        painter.drawImage(target, qimg)

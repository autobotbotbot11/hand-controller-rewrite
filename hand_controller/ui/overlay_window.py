from __future__ import annotations

from PyQt5.QtCore import QRect, Qt, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWidget

from ..config.settings import KeyboardConfig
from .payloads import OverlayPayload


class OverlayWindow(QWidget):
    def __init__(self, settings: KeyboardConfig | None = None) -> None:
        super().__init__()
        self.settings = settings or KeyboardConfig()
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
        if self.settings.show_skeleton:
            self._draw_skeleton(painter)
        if self.settings.show_pointers:
            self._draw_pointers(painter)
        self._draw_header(painter)
        self._draw_status(painter)
        self._draw_footer(painter)

    def _draw_keyboard(self, painter: QPainter) -> None:
        painter.setFont(QFont("Arial", self.settings.key_label_font_px))
        for key in self.payload.keyboard_keys:
            highlighted = key.label in self.payload.highlight_labels
            fill = QColor(0, 0, 0, 155) if not highlighted else QColor(0, 120, 220, 185)
            border = QColor(255, 255, 255, 210) if highlighted else QColor(185, 185, 185, 180)

            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(border, self.settings.key_border_px if not highlighted else self.settings.key_hover_border_px))
            rect = QRect(key.x1, key.y1, key.x2 - key.x1, key.y2 - key.y1)
            painter.drawRect(rect)

            label = "SPC" if key.label == "SPACE" else key.label
            painter.setPen(QColor(255, 255, 255, 230))
            painter.drawText(rect, Qt.AlignCenter, label)

    def _draw_skeleton(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(0, 200, 255, 180), self.settings.skeleton_stroke_px))
        for x1, y1, x2, y2 in self.payload.skeleton_lines:
            painter.drawLine(x1, y1, x2, y2)

    def _draw_pointers(self, painter: QPainter) -> None:
        radius = self.settings.pointer_radius_px
        painter.setPen(QPen(QColor(0, 255, 255, 230), self.settings.pointer_stroke_px))
        painter.setBrush(QBrush(QColor(0, 255, 255, 90)))
        painter.setFont(QFont("Arial", self.settings.pointer_label_font_px, QFont.Bold))
        for pointer in self.payload.finger_points:
            painter.drawEllipse(pointer.x - radius, pointer.y - radius, radius * 2, radius * 2)
            if pointer.hand_label:
                painter.setPen(QColor(255, 255, 255, 230))
                painter.drawText(pointer.x + radius + 3, pointer.y - max(4, radius // 2), pointer.hand_label)
                painter.setPen(QPen(QColor(0, 255, 255, 230), self.settings.pointer_stroke_px))

    def _draw_header(self, painter: QPainter) -> None:
        painter.setFont(QFont("Arial", self.settings.header_font_px))
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
        width = min(self.width() - 40, self.settings.status_panel_max_width_px)
        height = 30 + max(0, len(lines) - 1) * self.settings.status_line_height_px
        rect = QRect(x, y, width, height)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.setPen(QPen(QColor(0, 0, 0, 0), 0))
        painter.drawRect(rect)

        painter.setFont(QFont("Arial", self.settings.status_font_px))
        painter.setPen(QColor(255, 235, 190, 240))
        line_y = y + 20
        for line in lines:
            painter.drawText(x + 10, line_y, line)
            line_y += self.settings.status_line_height_px

    def _draw_footer(self, painter: QPainter) -> None:
        if not self.payload.footer_hint:
            return
        painter.setFont(QFont("Arial", self.settings.footer_font_px))
        painter.setPen(QColor(190, 190, 190, 220))
        painter.drawText(20, self.height() - 24, self.payload.footer_hint)

    def _draw_selfie(self, painter: QPainter) -> None:
        if not self.settings.show_selfie:
            return
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
        target = QRect(20, 110, self.settings.selfie_width_px, self.settings.selfie_height_px)
        painter.drawImage(target, qimg)

from __future__ import annotations

from PyQt5.QtCore import QRect, QRectF, Qt, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPainterPath, QPen
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

    @pyqtSlot(object)
    def apply_settings(self, settings: object) -> None:
        if not isinstance(settings, KeyboardConfig):
            return
        self.settings = settings
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
        self._draw_gesture_command(painter)

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

    def _selfie_target_rect(self) -> QRect:
        margin = 20
        x = margin
        y = 110
        if self.settings.selfie_position == "top_right":
            x = self.width() - self.settings.selfie_width_px - margin
        elif self.settings.selfie_position == "bottom_left":
            y = self.height() - self.settings.selfie_height_px - 48
        elif self.settings.selfie_position == "bottom_right":
            x = self.width() - self.settings.selfie_width_px - margin
            y = self.height() - self.settings.selfie_height_px - 48
        return QRect(x, y, self.settings.selfie_width_px, self.settings.selfie_height_px)

    def _draw_selfie_placeholder(self, painter: QPainter, target: QRect) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255, 235), 2))
        painter.setBrush(Qt.NoBrush)

        icon_w = min(72, max(40, target.width() // 3))
        icon_h = int(icon_w * 0.7)
        body = QRectF(
            target.center().x() - icon_w / 2,
            target.center().y() - icon_h / 2,
            icon_w,
            icon_h,
        )
        painter.drawRoundedRect(body, 8, 8)

        lens_size = min(icon_h * 0.45, icon_w * 0.34)
        lens = QRectF(
            target.center().x() - lens_size / 2,
            target.center().y() - lens_size / 2,
            lens_size,
            lens_size,
        )
        painter.drawEllipse(lens)

        top = QRectF(body.left() + icon_w * 0.18, body.top() - 10, icon_w * 0.36, 10)
        painter.drawRoundedRect(top, 5, 5)
        painter.restore()

    def _draw_gesture_command(self, painter: QPainter) -> None:
        if not self.settings.show_gesture_command or not self.payload.gesture_command_text:
            return

        painter.setFont(QFont("Arial", max(16, self.settings.header_font_px + 2), QFont.Bold))
        metrics = painter.fontMetrics()
        text = self.payload.gesture_command_text
        text_width = metrics.horizontalAdvance(text)
        width = text_width + 32
        height = metrics.height() + 20
        x = (self.width() - width) // 2

        position = self.settings.gesture_command_position
        if position == "center":
            y = (self.height() - height) // 2
        elif position == "bottom":
            y = self.height() - height - 56
        else:
            y = 68

        rect = QRect(x, y, width, height)
        painter.setBrush(QBrush(QColor(0, 0, 0, 175)))
        painter.setPen(QPen(QColor(255, 255, 255, 0), 0))
        painter.drawRoundedRect(rect, 14, 14)
        painter.setPen(QColor(255, 255, 255, 235))
        painter.drawText(rect, Qt.AlignCenter, text)

    def _draw_selfie(self, painter: QPainter) -> None:
        if not self.settings.show_selfie:
            return
        target = self._selfie_target_rect()

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        panel_path = QPainterPath()
        panel_path.addRoundedRect(QRectF(target), 18, 18)
        painter.setPen(QPen(QColor(255, 255, 255, 75), 1))
        painter.setBrush(QBrush(QColor(0, 0, 0, 230)))
        painter.drawPath(panel_path)

        frame = self.payload.selfie_frame
        if frame is not None:
            try:
                import cv2
            except ModuleNotFoundError:
                frame = None

        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            inset = target.adjusted(3, 3, -3, -3)
            clip_path = QPainterPath()
            clip_path.addRoundedRect(QRectF(inset), 15, 15)
            painter.setClipPath(clip_path)
            painter.drawImage(inset, qimg)
        else:
            self._draw_selfie_placeholder(painter, target)
        painter.restore()

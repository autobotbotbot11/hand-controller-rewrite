from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from PyQt5.QtCore import QPointF, QRectF, QSize, Qt, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap, QPolygonF
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import AppConfig, build_factory_default_config
from .overlay_window import OverlayWindow
from .signals import OverlaySignalBus


WorkerFn = Callable[[OverlaySignalBus, threading.Event, AppConfig, int, int], None]

PAGE_ORDER = ["GENERAL", "CAMERA", "DISPLAY", "KEYBOARD", "MOUSE"]
SELFIE_POSITIONS = [("Top Left", "top_left"), ("Top Right", "top_right"), ("Bottom Left", "bottom_left"), ("Bottom Right", "bottom_right")]
GESTURE_COMMAND_POSITIONS = [("Top", "top"), ("Center", "center"), ("Bottom", "bottom")]
HELP_TEXT = {
    "mouse_sensitivity": "Adjusts how strongly hand movement affects cursor movement.",
    "mouse_smoothness": "Adds more smoothing to reduce mouse jitter.",
    "mouse_dead_zone": "Ignores very small hand movement near the resting position.",
    "tap_sensitivity": "Controls how close thumb and index finger must be to count as a keyboard tap.",
    "tap_cooldown": "Minimum delay before another keyboard tap is accepted.",
    "keyboard_enable": "Turns the virtual keyboard feature on or off.",
    "camera_enable": "Turns camera input on or off.",
    "camera_source": "Selects which available camera device the app should use.",
    "show_hand_skeleton": "Shows or hides hand skeleton lines on the overlay.",
    "hand_skeleton_thickness": "Adjusts skeleton line thickness.",
    "show_live_selfie": "Shows or hides the live selfie preview on the overlay.",
    "selfie_position": "Chooses where the selfie preview appears on screen.",
    "selfie_size": "Adjusts the size of the live selfie preview.",
    "show_gesture_command": "Shows or hides text feedback for recognized gestures.",
    "gesture_command_position": "Chooses where the gesture feedback text appears on screen.",
    "minimize_after_launch": "Minimizes the window to the taskbar after launch.",
}


class SidebarPillButton(QPushButton):
    def __init__(self, text: str, *, icon_kind: str, launch: bool) -> None:
        super().__init__(text)
        self.icon_kind = icon_kind
        self.launch = launch
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setMinimumHeight(58 if launch else 40)

    def set_icon_kind(self, icon_kind: str) -> None:
        self.icon_kind = icon_kind
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(160, 58 if self.launch else 40)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = 18 if self.launch else 8

        fill = QColor("#ececef" if self.launch else "#efeff1")
        if self.launch and self.icon_kind == "stop":
            fill = QColor("#eee5e5")
        if self.isDown():
            fill = fill.darker(104)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(rect, radius, radius)

        icon_center_x = 26 if self.launch else 18
        icon_center_y = rect.center().y()

        painter.setBrush(QBrush(QColor("#111111")))
        painter.setPen(QPen(QColor("#111111"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        if self.icon_kind == "play":
            triangle = QPolygonF(
                [
                    QPointF(icon_center_x - 6, icon_center_y - 9),
                    QPointF(icon_center_x - 6, icon_center_y + 9),
                    QPointF(icon_center_x + 9, icon_center_y),
                ]
            )
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(triangle)
        elif self.icon_kind == "stop":
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(icon_center_x - 7, icon_center_y - 7, 14, 14), 3, 3)
        elif self.icon_kind == "close":
            painter.drawLine(QPointF(icon_center_x - 6, icon_center_y - 6), QPointF(icon_center_x + 6, icon_center_y + 6))
            painter.drawLine(QPointF(icon_center_x + 6, icon_center_y - 6), QPointF(icon_center_x - 6, icon_center_y + 6))

        text_x = 52 if self.launch else 38
        painter.setPen(QColor("#111111"))
        painter.setFont(QFont("Segoe UI", 10 if self.launch else 9, QFont.Bold))
        painter.drawText(QRectF(text_x, 0, rect.width() - text_x - 14, rect.height()), Qt.AlignVCenter | Qt.AlignLeft, self.text())


class ToggleSwitch(QCheckBox):
    def __init__(self) -> None:
        super().__init__()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(42, 22)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(42, 22)

    def hitButton(self, pos) -> bool:  # noqa: N802
        return self.rect().contains(pos)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        track_rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        track_color = QColor("#19e85c" if self.isChecked() else "#d2d2d7")
        knob_color = QColor("#d9d9dc" if self.isChecked() else "#f4f4f6")
        border_color = QColor("#19e85c" if self.isChecked() else "#cdced3")

        painter.setPen(QPen(border_color, 1))
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(track_rect, track_rect.height() / 2.0, track_rect.height() / 2.0)

        knob_size = track_rect.height() - 4
        knob_x = track_rect.right() - knob_size - 2 if self.isChecked() else track_rect.left() + 2
        knob_rect = QRectF(knob_x, track_rect.top() + 2, knob_size, knob_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(knob_color))
        painter.drawEllipse(knob_rect)


class NavButton(QPushButton):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setCheckable(True)
        self.setFixedHeight(38)

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setChecked(active)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        if self._active:
            pill_rect = QRectF(rect.left() + 5, rect.top() + 1, rect.width() - 5, rect.height() - 2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#efeff4")))
            painter.drawRoundedRect(pill_rect, 8, 8)

            indicator_rect = QRectF(pill_rect.left() + 2, rect.top() + 11, 2, rect.height() - 22)
            painter.setBrush(QBrush(QColor("#7282ff")))
            painter.drawRoundedRect(indicator_rect, 1.0, 1.0)

        painter.setPen(QColor("#111111" if self._active else "#77777f"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold if self._active else QFont.DemiBold))
        painter.drawText(
            QRectF(rect.left() + 18, rect.top(), rect.width() - 18, rect.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            self.text(),
        )


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        config: AppConfig,
        worker_fn: WorkerFn,
        ui_mode_label: str = "Control Panel",
        info_text: str | None = None,
        start_button_label: str = "LAUNCH",
        stop_button_label: str = "STOP",
    ) -> None:
        super().__init__()
        self.base_config = config
        self.working_config = config
        self.worker_fn = worker_fn
        self.ui_mode_label = ui_mode_label
        self.info_text = info_text
        self.start_button_label = start_button_label
        self.stop_button_label = stop_button_label

        self.overlay: OverlayWindow | None = None
        self.overlay_bus: OverlaySignalBus | None = None
        self.worker_thread: threading.Thread | None = None
        self.stop_event: threading.Event | None = None
        self.running = False

        self.page_stack: QStackedWidget | None = None
        self.nav_buttons: dict[str, QPushButton] = {}
        self.controls: dict[str, QWidget] = {}
        self.value_labels: dict[str, QLabel] = {}
        self.camera_sources = self._detect_camera_sources()

        self._init_ui()
        self._sync_widgets_from_config()

    def _init_ui(self) -> None:
        self.setWindowTitle("Hand Controller")
        self.resize(980, 720)
        self.setMinimumSize(860, 620)

        central = QWidget()
        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        central.setLayout(root)
        self.setCentralWidget(central)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(188)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(14, 22, 14, 14)
        sidebar_layout.setSpacing(10)
        sidebar.setLayout(sidebar_layout)

        logo = self._build_logo_widget()
        logo.setObjectName("logoLabel")
        sidebar_layout.addWidget(logo)

        sidebar_layout.addWidget(self._section_header("START PROGRAM"))
        self.controls["launch"] = self._pill_button(self.start_button_label.upper(), launch=True)
        self.controls["launch"].clicked.connect(self.toggle_worker)
        sidebar_layout.addWidget(self.controls["launch"])

        sidebar_layout.addSpacing(22)
        sidebar_layout.addWidget(self._section_header("NAVIGATE"))
        nav_group = QButtonGroup(self)
        nav_group.setExclusive(True)
        for page in PAGE_ORDER:
            button = NavButton(page)
            button.clicked.connect(lambda checked=False, name=page: self._set_active_page(name))
            nav_group.addButton(button)
            sidebar_layout.addWidget(button)
            self.nav_buttons[page] = button

        sidebar_layout.addStretch(1)
        self.controls["close"] = self._pill_button("CLOSE", launch=False)
        self.controls["close"].clicked.connect(self.close)
        sidebar_layout.addWidget(self.controls["close"])

        content = QFrame()
        content.setObjectName("contentFrame")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(12, 18, 18, 16)
        content_layout.setSpacing(0)
        content.setLayout(content_layout)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")
        self.page_stack.addWidget(self._page_general())
        self.page_stack.addWidget(self._page_camera())
        self.page_stack.addWidget(self._page_display())
        self.page_stack.addWidget(self._page_keyboard())
        self.page_stack.addWidget(self._page_mouse())
        content_layout.addWidget(self.page_stack)

        root.addWidget(sidebar)
        root.addWidget(content, 1)

        self.setStyleSheet(
            """
            QWidget { background: #f8f8fb; color: #111111; font-family: "Segoe UI"; }
            QFrame { background: #ffffff; }
            QFrame#sidebarFrame { background: #ffffff; border-right: 1px solid #d9dbe3; }
            QFrame#contentFrame { background: #f8f8fb; }
            QStackedWidget#pageStack { background: #f8f8fb; }
            QWidget#pageShell, QWidget#scrollInner, QWidget#rowWrapper { background: transparent; }
            QLabel#logoLabel { margin-bottom: 10px; }
            QLabel#sectionHeader { font-size: 13px; font-weight: 800; letter-spacing: 0.2px; background: transparent; }
            QLabel#pageTitle { font-size: 17px; font-weight: 800; margin: 0 0 6px 2px; background: transparent; }
            QLabel#fieldLabel { font-size: 13px; font-weight: 700; background: transparent; }
            QLabel#valueLabel { font-size: 11px; color: #b5b5bc; background: transparent; }
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget { border: none; background: #f8f8fb; }
            QFrame#card { border: 1px solid #dfe0e7; border-radius: 24px; background: #f4f4f7; }
            QPushButton#outlineButton { background: #ffffff; border: 1px solid #d8d8dd; border-radius: 2px; min-height: 22px; padding: 1px 8px; font-size: 10px; color: #7a7a80; }
            QPushButton#dangerButton { background: #ffffff; border: 1px solid #e14747; border-radius: 5px; min-height: 22px; padding: 1px 8px; font-size: 10px; font-weight: 700; color: #e14747; }
            QComboBox { background: #ffffff; border: 1px solid #d8d8dd; border-radius: 2px; min-height: 22px; padding: 1px 8px; font-size: 10px; color: #73737a; }
            QSlider::groove:horizontal { height: 4px; background: #d7d9e2; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #9aa5ff; border-radius: 2px; }
            QSlider::handle:horizontal { background: #d9d9dd; width: 14px; margin: -6px 0; border-radius: 7px; border: 1px solid #ccced4; }
            QToolButton { border: 1px solid #1b1b1b; border-radius: 7px; min-width: 14px; max-width: 14px; min-height: 14px; max-height: 14px; padding: 0; font-size: 9px; font-weight: 700; color: #1b1b1b; background: transparent; }
            """
        )

        self._set_active_page("GENERAL")

    def _section_header(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionHeader")
        return label

    def _build_logo_widget(self) -> QLabel:
        label = QLabel()
        candidates = [
            Path(__file__).resolve().parents[2] / "assets" / "touch-logo.png",
            Path(__file__).resolve().parents[2] / "assets" / "logo.png",
            Path(__file__).resolve().parents[2] / "touch-logo.png",
            Path(__file__).resolve().parents[2] / "logo.png",
        ]
        logo_path = next((path for path in candidates if path.exists()), None)
        if logo_path is not None:
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                label.setPixmap(
                    pixmap.scaled(
                        132,
                        64,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
                return label

        label.setText(
            '<span style="font-size:44px; font-weight:800; color:#407af6;">TOU</span>'
            '<span style="font-size:44px; font-weight:800; color:#57d6d0;">CH</span>'
        )
        label.setTextFormat(Qt.RichText)
        return label

    def _pill_button(self, text: str, *, launch: bool) -> QPushButton:
        button = SidebarPillButton(
            text,
            icon_kind="play" if launch else "close",
            launch=launch,
        )
        return button

    def _make_page(self, title: str, card: QWidget) -> QWidget:
        page = QWidget()
        page.setObjectName("pageShell")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        page.setLayout(layout)

        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        inner = QWidget()
        inner.setObjectName("scrollInner")
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 20)
        inner_layout.setSpacing(8)
        inner.setLayout(inner_layout)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        inner_layout.addWidget(title_label)
        inner_layout.addWidget(card, 0, Qt.AlignTop)
        inner_layout.addStretch(1)

        scroll.setWidget(inner)
        layout.addWidget(scroll)
        return page

    def _card(self) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(620)
        card.setMaximumWidth(760)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(22)
        card.setLayout(layout)
        return card, layout

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _value(self) -> QLabel:
        label = QLabel("")
        label.setObjectName("valueLabel")
        return label

    def _help(self, key: str) -> QToolButton:
        button = QToolButton()
        button.setText("?")
        button.setToolTip(HELP_TEXT[key])
        return button

    def _switch(self, key: str) -> QCheckBox:
        box = ToggleSwitch()
        self.controls[key] = box
        return box

    def _combo(self, key: str, width: int = 150) -> QComboBox:
        combo = QComboBox()
        combo.setFixedWidth(width)
        self.controls[key] = combo
        return combo

    def _slider(self, key: str, minimum: int, maximum: int) -> QSlider:
        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        self.controls[key] = slider
        return slider

    def _outline(self, key: str, text: str, *, danger: bool = False, width: int = 86) -> QPushButton:
        button = QPushButton(text)
        button.setFixedWidth(width)
        button.setObjectName("dangerButton" if danger else "outlineButton")
        self.controls[key] = button
        return button

    def _row(self, layout: QVBoxLayout, text: str, control: QWidget, *, help_key: str | None = None, value_label: QLabel | None = None, slider: bool = False) -> None:
        wrapper = QWidget()
        wrapper.setObjectName("rowWrapper")
        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(8)
        wrapper.setLayout(wrapper_layout)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)
        top.addWidget(self._label(text))
        if help_key:
            top.addWidget(self._help(help_key))
        top.addStretch(1)
        if value_label is not None:
            top.addWidget(value_label)
        elif not slider:
            top.addWidget(control)
        wrapper_layout.addLayout(top)

        if slider:
            wrapper_layout.addWidget(control)
        layout.addWidget(wrapper)

    def _page_general(self) -> QWidget:
        card, layout = self._card()
        lang = self._combo("language", width=104)
        lang.addItems(["English"])
        lang.currentTextChanged.connect(lambda text: self._update_general(language=text))
        self._row(layout, "Language", lang)

        theme = self._combo("theme", width=134)
        theme.addItems(["System Default", "Light"])
        theme.currentTextChanged.connect(lambda text: self._update_general(theme=text))
        self._row(layout, "Theme", theme)

        manual = self._outline("manual", "OPEN", width=58)
        manual.clicked.connect(lambda: QMessageBox.information(self, "User Manual", "Placeholder pa lang ito."))
        self._row(layout, "User Manual", manual)

        minimize_after_launch = self._switch("minimize_after_launch")
        minimize_after_launch.toggled.connect(lambda checked: self._update_general(minimize_after_launch=checked))
        self._row(layout, "Minimize After Launch", minimize_after_launch, help_key="minimize_after_launch")

        reset = self._outline("reset", "Reset", danger=True, width=58)
        reset.clicked.connect(self._reset_to_factory_defaults)
        self._row(layout, "Reset to Default", reset)
        return self._make_page("General", card)

    def _page_camera(self) -> QWidget:
        card, layout = self._card()
        camera_enable = self._switch("camera_enable")
        camera_enable.toggled.connect(lambda checked: self._update_camera(enabled=checked))
        self._row(layout, "Enable Camera", camera_enable, help_key="camera_enable")

        source = self._combo("camera_source", width=138)
        for label, index in self.camera_sources:
            source.addItem(label, index)
        source.currentIndexChanged.connect(self._camera_source_changed)
        self._row(layout, "Camera Source", source, help_key="camera_source")
        return self._make_page("Camera", card)

    def _page_display(self) -> QWidget:
        card, layout = self._card()
        skeleton = self._switch("show_hand_skeleton")
        skeleton.toggled.connect(lambda checked: self._update_keyboard(show_skeleton=checked))
        self._row(layout, "Show Hand Skeleton", skeleton, help_key="show_hand_skeleton")

        skeleton_value = self._value()
        self.value_labels["skeleton"] = skeleton_value
        skeleton_slider = self._slider("skeleton_thickness", 1, 10)
        skeleton_slider.valueChanged.connect(self._display_skeleton_thickness_changed)
        self._row(layout, "Hand Skeleton Thickness", skeleton_slider, help_key="hand_skeleton_thickness", value_label=skeleton_value, slider=True)

        selfie = self._switch("show_live_selfie")
        selfie.toggled.connect(lambda checked: self._update_keyboard(show_selfie=checked))
        self._row(layout, "Show Live Selfie", selfie, help_key="show_live_selfie")

        selfie_position = self._combo("selfie_position")
        for label, value in SELFIE_POSITIONS:
            selfie_position.addItem(label, value)
        selfie_position.currentIndexChanged.connect(self._selfie_position_changed)
        self._row(layout, "Selfie Position", selfie_position, help_key="selfie_position")

        selfie_size_value = self._value()
        self.value_labels["selfie"] = selfie_size_value
        selfie_size = self._slider("selfie_size", 50, 160)
        selfie_size.valueChanged.connect(self._display_selfie_size_changed)
        self._row(layout, "Selfie Size", selfie_size, help_key="selfie_size", value_label=selfie_size_value, slider=True)

        gesture = self._switch("show_gesture_command")
        gesture.toggled.connect(lambda checked: self._update_keyboard(show_gesture_command=checked))
        self._row(layout, "Show Gesture Command", gesture, help_key="show_gesture_command")

        gesture_position = self._combo("gesture_command_position")
        for label, value in GESTURE_COMMAND_POSITIONS:
            gesture_position.addItem(label, value)
        gesture_position.currentIndexChanged.connect(self._gesture_command_position_changed)
        self._row(layout, "Gesture Command Position", gesture_position, help_key="gesture_command_position")
        return self._make_page("Display", card)

    def _page_keyboard(self) -> QWidget:
        card, layout = self._card()
        tap_sens_value = self._value()
        self.value_labels["tap_sensitivity"] = tap_sens_value
        tap_sens = self._slider("tap_sensitivity", 10, 80)
        tap_sens.valueChanged.connect(self._keyboard_tap_sensitivity_changed)
        self._row(layout, "Tap Sensitivity", tap_sens, help_key="tap_sensitivity", value_label=tap_sens_value, slider=True)

        tap_cooldown_value = self._value()
        self.value_labels["tap_cooldown"] = tap_cooldown_value
        tap_cooldown = self._slider("tap_cooldown", 0, 600)
        tap_cooldown.valueChanged.connect(self._keyboard_tap_cooldown_changed)
        self._row(layout, "Tap Cooldown", tap_cooldown, help_key="tap_cooldown", value_label=tap_cooldown_value, slider=True)

        keyboard_enable = self._switch("keyboard_enable")
        keyboard_enable.toggled.connect(lambda checked: self._update_keyboard(virtual_keyboard_enabled=checked))
        self._row(layout, "Enable Virtual Keyboard Control", keyboard_enable, help_key="keyboard_enable")
        return self._make_page("Keyboard", card)

    def _page_mouse(self) -> QWidget:
        card, layout = self._card()
        sensitivity_value = self._value()
        self.value_labels["mouse_sensitivity"] = sensitivity_value
        sensitivity = self._slider("mouse_sensitivity", 30, 200)
        sensitivity.valueChanged.connect(self._mouse_sensitivity_changed)
        self._row(layout, "Sensitivity", sensitivity, help_key="mouse_sensitivity", value_label=sensitivity_value, slider=True)

        smooth_value = self._value()
        self.value_labels["mouse_smoothness"] = smooth_value
        smooth = self._slider("mouse_smoothness", 10, 90)
        smooth.valueChanged.connect(self._mouse_smoothness_changed)
        self._row(layout, "Smoothness", smooth, help_key="mouse_smoothness", value_label=smooth_value, slider=True)

        dead_value = self._value()
        self.value_labels["mouse_dead_zone"] = dead_value
        dead_zone = self._slider("mouse_dead_zone", 0, 100)
        dead_zone.valueChanged.connect(self._mouse_dead_zone_changed)
        self._row(layout, "Dead Zone", dead_zone, help_key="mouse_dead_zone", value_label=dead_value, slider=True)
        return self._make_page("Mouse", card)

    def _set_active_page(self, page: str) -> None:
        if self.page_stack is None:
            return
        index = PAGE_ORDER.index(page)
        self.page_stack.setCurrentIndex(index)
        for name, button in self.nav_buttons.items():
            active = name == page
            if isinstance(button, NavButton):
                button.set_active(active)
            else:
                button.setChecked(active)

    def _update_launch_button(self) -> None:
        button = self.controls["launch"]
        button.setText(self.stop_button_label.upper() if self.running else self.start_button_label.upper())
        if isinstance(button, SidebarPillButton):
            button.set_icon_kind("stop" if self.running else "play")
        button.setProperty("running", "true" if self.running else "false")
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def _detect_camera_sources(self) -> list[tuple[str, int]]:
        try:
            import cv2
        except ModuleNotFoundError:
            return [("Default Webcam", 0)]
        sources: list[tuple[str, int]] = []
        api_pref = getattr(cv2, "CAP_DSHOW", 0)
        for index in range(5):
            cap = None
            try:
                cap = cv2.VideoCapture(index, api_pref)
                if cap.isOpened():
                    sources.append(("Default Webcam" if index == 0 else f"Camera {index}", index))
            except Exception:
                pass
            finally:
                try:
                    if cap is not None:
                        cap.release()
                except Exception:
                    pass
        return sources or [("Default Webcam", 0)]

    def _block(self, key: str, block: bool) -> None:
        widget = self.controls.get(key)
        if widget is not None:
            widget.blockSignals(block)

    def _sync_widgets_from_config(self) -> None:
        keys = [
            "language", "theme", "minimize_after_launch", "camera_enable", "camera_source",
            "show_hand_skeleton", "skeleton_thickness", "show_live_selfie", "selfie_position",
            "selfie_size", "show_gesture_command", "gesture_command_position",
            "tap_sensitivity", "tap_cooldown", "keyboard_enable",
            "mouse_sensitivity", "mouse_smoothness", "mouse_dead_zone",
        ]
        for key in keys:
            self._block(key, True)
        try:
            cast = self.working_config
            self.controls["language"].setCurrentText(cast.general.language)
            self.controls["theme"].setCurrentText(cast.general.theme)
            self.controls["minimize_after_launch"].setChecked(cast.general.minimize_after_launch)
            self.controls["camera_enable"].setChecked(cast.camera.enabled)
            idx = self.controls["camera_source"].findData(cast.camera.index)
            if idx < 0:
                self.controls["camera_source"].addItem(f"Camera {cast.camera.index}", cast.camera.index)
                idx = self.controls["camera_source"].findData(cast.camera.index)
            self.controls["camera_source"].setCurrentIndex(max(0, idx))
            self.controls["show_hand_skeleton"].setChecked(cast.keyboard.show_skeleton)
            self.controls["skeleton_thickness"].setValue(int(cast.keyboard.skeleton_stroke_px))
            self.controls["show_live_selfie"].setChecked(cast.keyboard.show_selfie)
            idx = self.controls["selfie_position"].findData(cast.keyboard.selfie_position)
            self.controls["selfie_position"].setCurrentIndex(max(0, idx))
            self.controls["selfie_size"].setValue(max(50, min(160, int(round((cast.keyboard.selfie_width_px / 320.0) * 100)))))
            self.controls["show_gesture_command"].setChecked(cast.keyboard.show_gesture_command)
            idx = self.controls["gesture_command_position"].findData(cast.keyboard.gesture_command_position)
            self.controls["gesture_command_position"].setCurrentIndex(max(0, idx))
            self.controls["tap_sensitivity"].setValue(int(round(cast.keyboard.index_pinch_threshold_px)))
            self.controls["tap_cooldown"].setValue(int(round(cast.keyboard.tap_cooldown_seconds * 1000)))
            self.controls["keyboard_enable"].setChecked(cast.keyboard.virtual_keyboard_enabled)
            self.controls["mouse_sensitivity"].setValue(int(round(cast.mouse_motion.sensitivity * 100)))
            self.controls["mouse_smoothness"].setValue(int(round(cast.mouse_motion.ema_alpha * 100)))
            self.controls["mouse_dead_zone"].setValue(int(round(cast.mouse_motion.wake_threshold_px * 10)))
        finally:
            for key in keys:
                self._block(key, False)

        self._display_skeleton_thickness_changed(self.controls["skeleton_thickness"].value())
        self._display_selfie_size_changed(self.controls["selfie_size"].value())
        self._keyboard_tap_sensitivity_changed(self.controls["tap_sensitivity"].value())
        self._keyboard_tap_cooldown_changed(self.controls["tap_cooldown"].value())
        self._mouse_sensitivity_changed(self.controls["mouse_sensitivity"].value())
        self._mouse_smoothness_changed(self.controls["mouse_smoothness"].value())
        self._mouse_dead_zone_changed(self.controls["mouse_dead_zone"].value())
        self._push_live_overlay_settings()
        self._update_launch_button()

    def _update_general(self, **kwargs) -> None:
        self.working_config = replace(self.working_config, general=replace(self.working_config.general, **kwargs))

    def _update_camera(self, **kwargs) -> None:
        self.working_config = replace(self.working_config, camera=replace(self.working_config.camera, **kwargs))

    def _update_keyboard(self, **kwargs) -> None:
        self.working_config = replace(self.working_config, keyboard=replace(self.working_config.keyboard, **kwargs))
        self._push_live_overlay_settings()

    def _update_mouse_motion(self, **kwargs) -> None:
        self.working_config = replace(self.working_config, mouse_motion=replace(self.working_config.mouse_motion, **kwargs))

    def _push_live_overlay_settings(self) -> None:
        if not self.running or self.overlay_bus is None:
            return
        try:
            self.overlay_bus.update_overlay_settings.emit(self.working_config.keyboard)
        except Exception:
            pass

    def _camera_source_changed(self, index: int) -> None:
        value = self.controls["camera_source"].itemData(index)
        if value is not None:
            self._update_camera(index=int(value))

    def _display_skeleton_thickness_changed(self, value: int) -> None:
        self.value_labels["skeleton"].setText(f"{value}px")
        self._update_keyboard(skeleton_stroke_px=value)

    def _display_selfie_size_changed(self, value: int) -> None:
        self.value_labels["selfie"].setText(f"{value}%")
        self._update_keyboard(selfie_width_px=int(round(320 * value / 100.0)), selfie_height_px=int(round(240 * value / 100.0)))

    def _selfie_position_changed(self, index: int) -> None:
        value = self.controls["selfie_position"].itemData(index)
        if value is not None:
            self._update_keyboard(selfie_position=str(value))

    def _gesture_command_position_changed(self, index: int) -> None:
        value = self.controls["gesture_command_position"].itemData(index)
        if value is not None:
            self._update_keyboard(gesture_command_position=str(value))

    def _keyboard_tap_sensitivity_changed(self, value: int) -> None:
        self.value_labels["tap_sensitivity"].setText(f"{value}px")
        self._update_keyboard(index_pinch_threshold_px=float(value))

    def _keyboard_tap_cooldown_changed(self, value: int) -> None:
        self.value_labels["tap_cooldown"].setText(f"{value} ms")
        self._update_keyboard(tap_cooldown_seconds=float(value) / 1000.0)

    def _mouse_sensitivity_changed(self, value: int) -> None:
        self.value_labels["mouse_sensitivity"].setText(f"{value / 100.0:.2f}x")
        self._update_mouse_motion(sensitivity=float(value) / 100.0)

    def _mouse_smoothness_changed(self, value: int) -> None:
        self.value_labels["mouse_smoothness"].setText(f"{value / 100.0:.2f}")
        self._update_mouse_motion(ema_alpha=float(value) / 100.0)

    def _mouse_dead_zone_changed(self, value: int) -> None:
        dead_zone = float(value) / 10.0
        self.value_labels["mouse_dead_zone"].setText(f"{dead_zone:.1f}px")
        self._update_mouse_motion(wake_threshold_px=dead_zone, sleep_threshold_px=max(0.0, round(dead_zone * 0.4, 2)))

    def _reset_to_factory_defaults(self) -> None:
        defaults = build_factory_default_config()
        self.working_config = replace(defaults, tuning_path=self.working_config.tuning_path)
        self._sync_widgets_from_config()

    @pyqtSlot()
    def toggle_worker(self) -> None:
        if self.running:
            self.stop_worker()
        else:
            self.start_worker()

    def start_worker(self) -> None:
        if self.running:
            return
        launch_config = self.working_config
        if not launch_config.camera.enabled:
            QMessageBox.warning(self, "Camera Disabled", "Enable Camera first before launching the app.")
            return
        self.overlay = OverlayWindow(launch_config.keyboard)
        self.overlay_bus = OverlaySignalBus()
        self.overlay_bus.update_overlay.connect(self.overlay.apply_payload)
        self.overlay_bus.update_overlay_settings.connect(self.overlay.apply_settings)
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(
            target=self.worker_fn,
            args=(self.overlay_bus, self.stop_event, launch_config, max(1, self.overlay.width()), max(1, self.overlay.height())),
            daemon=True,
        )
        self.worker_thread.start()
        self.running = True
        self._update_launch_button()
        if launch_config.general.minimize_after_launch:
            self.showMinimized()

    def stop_worker(self) -> None:
        if not self.running:
            return
        if self.stop_event is not None:
            self.stop_event.set()
        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        if self.overlay_bus is not None and self.overlay is not None:
            try:
                self.overlay_bus.update_overlay.disconnect(self.overlay.apply_payload)
            except Exception:
                pass
            try:
                self.overlay_bus.update_overlay_settings.disconnect(self.overlay.apply_settings)
            except Exception:
                pass
        if self.overlay is not None:
            self.overlay.close()
            self.overlay = None
        self.overlay_bus = None
        self.worker_thread = None
        self.stop_event = None
        self.running = False
        self._update_launch_button()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_worker()
        event.accept()

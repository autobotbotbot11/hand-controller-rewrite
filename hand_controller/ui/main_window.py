from __future__ import annotations

import threading
from collections.abc import Callable

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import AppConfig
from .overlay_window import OverlayWindow
from .signals import OverlaySignalBus


WorkerFn = Callable[[OverlaySignalBus, threading.Event, AppConfig, int, int], None]


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        config: AppConfig,
        worker_fn: WorkerFn,
        ui_mode_label: str = "UI Smoke",
        info_text: str | None = None,
        start_button_label: str = "Start UI Foundation",
    ) -> None:
        super().__init__()
        self.config = config
        self.worker_fn = worker_fn
        self.ui_mode_label = ui_mode_label
        self.info_text = info_text
        self.start_button_label = start_button_label

        self.overlay: OverlayWindow | None = None
        self.overlay_bus: OverlaySignalBus | None = None
        self.worker_thread: threading.Thread | None = None
        self.stop_event: threading.Event | None = None
        self.running = False

        self.status_label: QLabel | None = None
        self.start_button: QPushButton | None = None
        self.info_box: QTextEdit | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Hand Controller Rewrite")
        self.resize(860, 560)

        central = QWidget()
        root = QHBoxLayout()
        central.setLayout(root)
        self.setCentralWidget(central)

        left = QVBoxLayout()
        left.setContentsMargins(20, 20, 20, 20)
        left.setSpacing(14)

        title = QLabel("Hand Controller Rewrite")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        left.addWidget(title)

        subtitle = QLabel(f"Keyboard V1 Phase K1: {self.ui_mode_label}")
        subtitle.setFont(QFont("Arial", 11))
        left.addWidget(subtitle)

        self.status_label = QLabel("Status: Stopped")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #ff5555;")
        left.addWidget(self.status_label)

        self.start_button = QPushButton("Start UI Foundation")
        self.start_button.setText(self.start_button_label)
        self.start_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.start_button.setFixedHeight(46)
        self.start_button.setStyleSheet("background-color: #55aa55; color: white; border-radius: 6px;")
        self.start_button.clicked.connect(self.toggle_worker)
        left.addWidget(self.start_button)

        left.addStretch()
        root.addLayout(left, 1)

        right = QVBoxLayout()
        right.setContentsMargins(20, 20, 20, 20)
        right.setSpacing(12)

        summary = QGroupBox("Phase K1 Goal")
        summary_layout = QVBoxLayout()
        summary_layout.addWidget(QLabel(
            "Validate the real UI architecture before wiring the live CV loop into it:\n"
            "- control panel window\n"
            "- transparent fullscreen overlay\n"
            "- thread-safe signal bus\n"
            "- clean Start / Stop lifecycle"
        ))
        summary.setLayout(summary_layout)
        right.addWidget(summary)

        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlainText(
            self.info_text
            or (
                "Current behavior:\n"
                "- Start creates the transparent overlay window.\n"
                "- A background worker emits mock overlay payloads.\n"
                "- Stop cleanly stops the worker and closes the overlay.\n\n"
                "This is not the final keyboard runtime yet. It is the UI foundation step."
            )
        )
        right.addWidget(self.info_box, 1)

        root.addLayout(right, 2)

    @pyqtSlot()
    def toggle_worker(self) -> None:
        if self.running:
            self.stop_worker()
        else:
            self.start_worker()

    def start_worker(self) -> None:
        if self.running:
            return

        self.overlay = OverlayWindow(self.config.keyboard)
        self.overlay_bus = OverlaySignalBus()
        self.overlay_bus.update_overlay.connect(self.overlay.apply_payload)

        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(
            target=self.worker_fn,
            args=(
                self.overlay_bus,
                self.stop_event,
                self.config,
                max(1, self.overlay.width()),
                max(1, self.overlay.height()),
            ),
            daemon=True,
        )
        self.worker_thread.start()

        self.running = True
        self._set_status("Running", running=True)

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

        if self.overlay is not None:
            self.overlay.close()
            self.overlay = None

        self.overlay_bus = None
        self.worker_thread = None
        self.stop_event = None
        self.running = False
        self._set_status("Stopped", running=False)

    def _set_status(self, text: str, *, running: bool) -> None:
        if self.status_label is not None:
            self.status_label.setText(f"Status: {text}")
            self.status_label.setStyleSheet("color: #55ff55;" if running else "color: #ff5555;")
        if self.start_button is not None:
            if running:
                self.start_button.setText("Stop UI Foundation")
                self.start_button.setStyleSheet("background-color: #cc5555; color: white; border-radius: 6px;")
            else:
                self.start_button.setText(self.start_button_label)
                self.start_button.setStyleSheet("background-color: #55aa55; color: white; border-radius: 6px;")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_worker()
        event.accept()

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import threading

from ..config.settings import RUNTIME_APP_DIR


_LOG_LOCK = threading.Lock()
_LOG_PATH = RUNTIME_APP_DIR / "HandController.log"


def diagnostics_enabled() -> bool:
    return bool(getattr(sys, "frozen", False))


def diagnostics_log_path() -> Path:
    return _LOG_PATH


def log_diagnostic(message: str) -> None:
    if not diagnostics_enabled():
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"

    with _LOG_LOCK:
        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line)

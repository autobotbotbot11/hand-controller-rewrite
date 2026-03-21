from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 640
    height: int = 480


@dataclass(slots=True, frozen=True)
class MouseMotionConfig:
    sensitivity: float = 0.95
    smoothing_window: int = 2
    anchor_alpha: float = 1.0
    ema_alpha: float = 0.58
    wake_threshold_px: float = 3.20
    sleep_threshold_px: float = 1.25
    micro_jitter_px: float = 0.90
    gain_exponent: float = 1.02
    accel_start_px: float = 5.0
    fast_gain: float = 1.10
    spike_clamp_px: float = 48.0
    reanchor_distance_px: float = 140.0
    max_step_px: float = 30.0
    move_timeout: float = 0.35


@dataclass(slots=True, frozen=True)
class HandTrackerConfig:
    max_num_hands: int = 2
    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.7
    mirror_input: bool = True


@dataclass(slots=True, frozen=True)
class HandSelectorConfig:
    switch_margin: float = 0.18
    lost_grace_seconds: float = 0.30
    centroid_switch_px: float = 85.0


@dataclass(slots=True, frozen=True)
class MLConfig:
    enabled: bool = True
    accepted_action_labels: tuple[str, ...] = ("toggle", "hold", "undo", "redo")
    ignored_behavior_labels: tuple[str, ...] = ("left_click", "right_click", "idle")


@dataclass(slots=True, frozen=True)
class AppConfig:
    python_version: str
    camera: CameraConfig
    tracker: HandTrackerConfig
    selector: HandSelectorConfig
    mouse_motion: MouseMotionConfig
    ml: MLConfig


def build_default_config() -> AppConfig:
    return AppConfig(
        python_version="3.11",
        camera=CameraConfig(),
        tracker=HandTrackerConfig(),
        selector=HandSelectorConfig(),
        mouse_motion=MouseMotionConfig(),
        ml=MLConfig(),
    )

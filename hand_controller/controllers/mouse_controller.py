from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import math

from ..config.settings import MouseMotionConfig
from .actions import MoveRelative


@dataclass(slots=True)
class MouseMotionState:
    prev_x: float | None = None
    prev_y: float | None = None
    filtered_x: float | None = None
    filtered_y: float | None = None
    last_seen: float = 0.0
    deltas: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=2))
    smooth_dx: float = 0.0
    smooth_dy: float = 0.0
    motion_awake: bool = False


class MouseController:
    """Movement-only mouse controller for Phase 4."""

    def __init__(self, screen_w: int, screen_h: int, settings: MouseMotionConfig | None = None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.settings = settings or MouseMotionConfig()
        self.state = MouseMotionState(deltas=deque(maxlen=self.settings.smoothing_window))

    def _reset_motion(self) -> None:
        self.state.prev_x = None
        self.state.prev_y = None
        self.state.filtered_x = None
        self.state.filtered_y = None
        self.state.last_seen = 0.0
        self.state.deltas.clear()
        self.state.smooth_dx = 0.0
        self.state.smooth_dy = 0.0
        self.state.motion_awake = False

    def _filter_anchor(self, x: float, y: float) -> tuple[float, float]:
        alpha = self.settings.anchor_alpha
        if self.state.filtered_x is None or self.state.filtered_y is None or alpha >= 0.999:
            self.state.filtered_x = x
            self.state.filtered_y = y
        else:
            self.state.filtered_x = alpha * x + (1.0 - alpha) * self.state.filtered_x
            self.state.filtered_y = alpha * y + (1.0 - alpha) * self.state.filtered_y
        return self.state.filtered_x, self.state.filtered_y

    def _apply_motion_gate(self, dx: float, dy: float) -> tuple[float, float]:
        magnitude = math.hypot(dx, dy)

        if self.state.motion_awake:
            if magnitude <= self.settings.sleep_threshold_px:
                self.state.motion_awake = False
                self.state.smooth_dx = 0.0
                self.state.smooth_dy = 0.0
                self.state.deltas.clear()
                return 0.0, 0.0
        else:
            if magnitude < self.settings.wake_threshold_px:
                return 0.0, 0.0
            self.state.motion_awake = True

        if abs(dx) < self.settings.micro_jitter_px:
            dx = 0.0
        if abs(dy) < self.settings.micro_jitter_px:
            dy = 0.0

        return dx, dy

    def _shape_delta(self, dx: float, dy: float) -> tuple[float, float]:
        magnitude = math.hypot(dx, dy)
        if magnitude <= 1e-6:
            return 0.0, 0.0

        if magnitude > self.settings.spike_clamp_px:
            scale = self.settings.spike_clamp_px / magnitude
            dx *= scale
            dy *= scale
            magnitude = self.settings.spike_clamp_px

        shaped_magnitude = magnitude ** self.settings.gain_exponent
        if magnitude >= self.settings.accel_start_px:
            shaped_magnitude *= self.settings.fast_gain

        scale = shaped_magnitude / magnitude
        return dx * scale, dy * scale

    def update(
        self,
        *,
        anchor_norm: tuple[float, float] | None,
        movement_enabled: bool,
        now: float,
    ) -> tuple[list[MoveRelative], str]:
        actions: list[MoveRelative] = []

        if anchor_norm is None:
            self._reset_motion()
            return actions, "Mouse | no active hand"

        if not movement_enabled:
            self._reset_motion()
            return actions, "Mouse | gated"

        x, y = anchor_norm

        if self.state.last_seen > 0.0 and (now - self.state.last_seen) > self.settings.move_timeout:
            self._reset_motion()

        filtered_x, filtered_y = self._filter_anchor(x, y)
        self.state.last_seen = now

        if self.state.prev_x is not None and self.state.prev_y is not None:
            raw_dx = (filtered_x - self.state.prev_x) * self.screen_w * self.settings.sensitivity
            raw_dy = (filtered_y - self.state.prev_y) * self.screen_h * self.settings.sensitivity

            jump_magnitude = math.hypot(raw_dx, raw_dy)
            if jump_magnitude >= self.settings.reanchor_distance_px:
                self._reset_motion()
                self.state.prev_x = filtered_x
                self.state.prev_y = filtered_y
                return actions, "Mouse | re-anchor"

            gated_dx, gated_dy = self._apply_motion_gate(raw_dx, raw_dy)
            shaped_dx, shaped_dy = self._shape_delta(gated_dx, gated_dy)

            alpha = self.settings.ema_alpha if self.state.motion_awake else 1.0
            self.state.smooth_dx = alpha * shaped_dx + (1.0 - alpha) * self.state.smooth_dx
            self.state.smooth_dy = alpha * shaped_dy + (1.0 - alpha) * self.state.smooth_dy

            self.state.deltas.append((self.state.smooth_dx, self.state.smooth_dy))
            avg_dx = sum(delta[0] for delta in self.state.deltas) / len(self.state.deltas)
            avg_dy = sum(delta[1] for delta in self.state.deltas) / len(self.state.deltas)

            avg_dx = max(-self.settings.max_step_px, min(self.settings.max_step_px, avg_dx))
            avg_dy = max(-self.settings.max_step_px, min(self.settings.max_step_px, avg_dy))

            move_dx = int(round(avg_dx))
            move_dy = int(round(avg_dy))

            if move_dx != 0 or move_dy != 0:
                actions.append(MoveRelative(move_dx, move_dy))

        self.state.prev_x = filtered_x
        self.state.prev_y = filtered_y

        status = "Mouse | moving" if self.state.motion_awake else "Mouse | ready"
        return actions, status

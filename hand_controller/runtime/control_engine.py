from __future__ import annotations

import time
from dataclasses import dataclass

from ..config.settings import AppConfig
from ..controllers import (
    KeyboardController,
    KeyboardModeToggleController,
    MouseController,
    execute_actions,
)
from ..controllers.actions import Action
from ..controllers.keyboard_controller import KeyboardUpdate
from ..gestures import (
    HandPinchDetector,
    MouseClickGestureState,
    MouseClickDetector,
    is_palm_facing_thumb_pinky,
)
from ..ml import MLPrediction, MLPredictor, MLControlAdapter
from ..runtime.state import Mode, RuntimeState
from ..vision.hand_selector import HandSelector
from ..vision.models import SelectedHands, VisionResult


MOVEMENT_ANCHOR_IDX = 5


def _movement_anchor_norm(hand) -> tuple[float, float]:
    point = hand.landmark(MOVEMENT_ANCHOR_IDX)
    return point.x, point.y


@dataclass(frozen=True, slots=True)
class ControlFrameResult:
    runtime_state: RuntimeState
    vision: VisionResult
    selected: SelectedHands
    click_state: MouseClickGestureState
    keyboard_update: KeyboardUpdate
    movement_status: str
    movement_enabled: bool
    click_freeze: bool
    ml_prediction: MLPrediction
    ml_status: str
    ml_available: bool
    ml_reason: str | None
    mode_toggle_status: str
    drag_active: bool


class LiveControlEngine:
    def __init__(self, config: AppConfig, *, screen_width: int, screen_height: int) -> None:
        self.config = config
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.mouse_controller = MouseController(
            screen_w=screen_width,
            screen_h=screen_height,
            motion_settings=config.mouse_motion,
            click_settings=config.mouse_click,
        )
        self.click_detector = MouseClickDetector(config.mouse_click)
        self.pinch_detector = HandPinchDetector(config.keyboard)
        self.keyboard_controller = KeyboardController(config.keyboard)
        self.mode_toggle_controller = KeyboardModeToggleController(config.keyboard)
        self.runtime_state = RuntimeState()
        self.selector = HandSelector(config.selector)
        self.ml_predictor, self.ml_reason = MLPredictor.try_create(config.ml)
        self.ml_adapter = MLControlAdapter(config.ml)
        self._last_mode = self.runtime_state.mode

    def _handle_mode_transition(self, now: float) -> tuple[list[Action], str | None]:
        actions: list[Action] = []
        status: str | None = None

        if self.runtime_state.mode == self._last_mode:
            return actions, status

        self.click_detector.reset()
        self.keyboard_controller.reset()
        mouse_actions, mouse_status = self.mouse_controller.update(
            anchor_norm=None,
            control_enabled=self.runtime_state.control_enabled,
            movement_allowed=False,
            click_enabled=False,
            click_state=MouseClickGestureState(),
            now=now,
        )
        actions.extend(mouse_actions)
        if mouse_actions:
            status = mouse_status

        self._last_mode = self.runtime_state.mode
        return actions, status

    def process_frame(
        self,
        vision: VisionResult,
        *,
        layout_width: int,
        layout_height: int,
        now: float | None = None,
    ) -> ControlFrameResult:
        now = time.time() if now is None else now

        selected = self.selector.select(vision.hands, vision.frame_width, vision.frame_height)
        active_hand = selected.primary
        palm_facing = (
            is_palm_facing_thumb_pinky(active_hand, mirrored_input=self.config.tracker.mirror_input)
            if active_hand is not None
            else False
        )
        self.runtime_state.active_hand_label = active_hand.label if active_hand is not None else None
        self.runtime_state.palm_facing = palm_facing

        pinch_states = self.pinch_detector.analyze(
            hands=vision.hands,
            frame_width=vision.frame_width,
            frame_height=vision.frame_height,
        )
        active_pinch_state = pinch_states.get(active_hand.label) if active_hand is not None else None

        if self.ml_predictor is not None:
            ml_prediction = self.ml_predictor.predict(active_hand)
        else:
            ml_prediction = MLPrediction(available=False, reason=self.ml_reason)
        ml_update = self.ml_adapter.update(ml_prediction, self.runtime_state, now)

        mode_toggle_update = self.mode_toggle_controller.update(
            state=self.runtime_state,
            active_hand=active_hand,
            palm_facing=palm_facing,
            pinch_state=active_pinch_state,
            now=now,
        )

        if self.runtime_state.mode != Mode.MOUSE:
            self.runtime_state.hold_active = False

        transition_actions, transition_status = self._handle_mode_transition(now)

        click_state = MouseClickGestureState()
        keyboard_update = KeyboardUpdate(
            layout=self.keyboard_controller.layout_for_frame(layout_width, layout_height),
            status="keyboard idle",
        )
        movement_status = transition_status or "idle"
        movement_enabled = False
        click_freeze = False
        action_queue = list(transition_actions)
        action_queue.extend(ml_update.actions)

        if self.runtime_state.mode == Mode.MOUSE:
            click_enabled = self.runtime_state.control_enabled and not self.runtime_state.hold_active
            if click_enabled:
                click_state = self.click_detector.analyze(
                    active_hand=active_hand,
                    frame_width=vision.frame_width,
                    frame_height=vision.frame_height,
                )
            else:
                self.click_detector.reset()

            anchor_norm = _movement_anchor_norm(active_hand) if active_hand is not None else None
            movement_enabled = (
                active_hand is not None
                and palm_facing
                and self.runtime_state.control_enabled
                and not self.runtime_state.hold_active
            )
            self.runtime_state.movement_frozen = not movement_enabled

            mouse_actions, mouse_status = self.mouse_controller.update(
                anchor_norm=anchor_norm,
                control_enabled=self.runtime_state.control_enabled,
                movement_allowed=movement_enabled,
                click_enabled=click_enabled,
                click_state=click_state,
                now=now,
            )
            action_queue.extend(mouse_actions)
            movement_status = transition_status or mouse_status
            click_freeze = click_enabled and (
                click_state.right_pressed
                or (click_state.left_pressed and not self.mouse_controller.state.drag_active)
            )
        else:
            self.click_detector.reset()
            self.runtime_state.movement_frozen = True

            if self.runtime_state.control_enabled:
                keyboard_update = self.keyboard_controller.update(
                    hands=vision.hands,
                    pinch_states=pinch_states,
                    frame_width=layout_width,
                    frame_height=layout_height,
                )
                action_queue.extend(keyboard_update.actions)
            else:
                keyboard_update = KeyboardUpdate(
                    layout=self.keyboard_controller.layout_for_frame(layout_width, layout_height),
                    status="keyboard control off",
                )

            mouse_actions, mouse_status = self.mouse_controller.update(
                anchor_norm=None,
                control_enabled=self.runtime_state.control_enabled,
                movement_allowed=False,
                click_enabled=False,
                click_state=MouseClickGestureState(),
                now=now,
            )
            action_queue.extend(mouse_actions)
            movement_status = transition_status or ("keyboard mode" if mouse_status == "Mouse | no active hand" else mouse_status)

        execute_actions(action_queue)

        return ControlFrameResult(
            runtime_state=self.runtime_state,
            vision=vision,
            selected=selected,
            click_state=click_state,
            keyboard_update=keyboard_update,
            movement_status=movement_status,
            movement_enabled=movement_enabled,
            click_freeze=click_freeze,
            ml_prediction=ml_prediction,
            ml_status=ml_update.status,
            ml_available=self.ml_predictor is not None,
            ml_reason=self.ml_reason,
            mode_toggle_status=mode_toggle_update.status,
            drag_active=self.mouse_controller.state.drag_active,
        )

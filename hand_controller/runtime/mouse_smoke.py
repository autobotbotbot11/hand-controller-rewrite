from __future__ import annotations

import time

from ..config.settings import AppConfig
from ..controllers import MouseController, execute_actions, get_screen_size
from ..gestures import is_palm_facing_thumb_pinky
from ..vision.camera import Camera
from ..vision.hand_selector import HandSelector
from ..vision.hand_tracker import HandTracker
from ..vision.models import DetectedHand, VisionResult


MOVEMENT_ANCHOR_IDX = 5
VISUAL_CURSOR_IDX = 8


def _movement_anchor_norm(hand: DetectedHand) -> tuple[float, float]:
    point = hand.landmark(MOVEMENT_ANCHOR_IDX)
    return point.x, point.y


def _visual_cursor_px(hand: DetectedHand, frame_width: int, frame_height: int) -> tuple[int, int]:
    point = hand.landmark(VISUAL_CURSOR_IDX)
    return int(point.x * frame_width), int(point.y * frame_height)


def _anchor_px(hand: DetectedHand, frame_width: int, frame_height: int) -> tuple[int, int]:
    point = hand.landmark(MOVEMENT_ANCHOR_IDX)
    return int(point.x * frame_width), int(point.y * frame_height)


def _draw_mouse_smoke(
    frame_bgr,
    *,
    vision: VisionResult,
    tracker: HandTracker,
    selector: HandSelector,
    mirrored_input: bool,
    movement_status: str,
    movement_enabled: bool,
) -> None:
    import cv2

    height, width = frame_bgr.shape[:2]
    selected = selector.select(vision.hands, width, height)

    for hand in vision.hands:
        is_primary = selected.primary is hand
        palm_facing = is_palm_facing_thumb_pinky(hand, mirrored_input=mirrored_input)
        line_color = (0, 180, 255) if is_primary else (0, 220, 120)

        for start_idx, end_idx in tracker.connections:
            start = hand.landmark(start_idx)
            end = hand.landmark(end_idx)
            x1 = int(start.x * width)
            y1 = int(start.y * height)
            x2 = int(end.x * width)
            y2 = int(end.y * height)
            cv2.line(frame_bgr, (x1, y1), (x2, y2), line_color, 2)

        for point in hand.landmarks:
            px = int(point.x * width)
            py = int(point.y * height)
            cv2.circle(frame_bgr, (px, py), 3, (255, 255, 255), -1)

        wrist = hand.landmark(0)
        wx = int(wrist.x * width)
        wy = int(wrist.y * height)
        cv2.putText(
            frame_bgr,
            f"{hand.label} palm={'yes' if palm_facing else 'no'}{' active' if is_primary else ''}",
            (wx + 10, wy - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (50, 255, 255),
            2,
            cv2.LINE_AA,
        )

    if selected.primary is not None:
        anchor_x, anchor_y = _anchor_px(selected.primary, width, height)
        cursor_x, cursor_y = _visual_cursor_px(selected.primary, width, height)
        cv2.circle(frame_bgr, (anchor_x, anchor_y), 10, (0, 140, 255), 2)
        cv2.circle(frame_bgr, (cursor_x, cursor_y), 10, (255, 255, 0), 2)
        cv2.putText(
            frame_bgr,
            "anchor",
            (anchor_x + 12, anchor_y + 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 140, 255),
            2,
            cv2.LINE_AA,
        )

    status_line = "  ".join(
        [
            f"hands={len(vision.hands)}",
            f"active={selected.primary.label if selected.primary else '-'}",
            f"movement={'on' if movement_enabled else 'off'}",
            movement_status,
            "press q to quit",
        ]
    )
    cv2.putText(
        frame_bgr,
        status_line,
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def run_mouse_smoke(config: AppConfig) -> None:
    import cv2

    screen_w, screen_h = get_screen_size()
    controller = MouseController(screen_w=screen_w, screen_h=screen_h, settings=config.mouse_motion)

    with Camera(
        index=config.camera.index,
        width=config.camera.width,
        height=config.camera.height,
    ) as camera, HandTracker(
        max_num_hands=config.tracker.max_num_hands,
        min_detection_confidence=config.tracker.min_detection_confidence,
        min_tracking_confidence=config.tracker.min_tracking_confidence,
    ) as tracker:
        selector = HandSelector(config.selector)

        if not camera.is_opened():
            raise RuntimeError("Unable to open the configured camera.")

        window_name = "Hand Controller Rewrite - Phase 4 Mouse Smoke"

        while True:
            ok, frame_bgr = camera.read()
            if not ok:
                continue

            if config.tracker.mirror_input:
                frame_bgr = cv2.flip(frame_bgr, 1)

            vision = tracker.track_bgr_frame(frame_bgr)
            selected = selector.select(vision.hands, vision.frame_width, vision.frame_height)
            active_hand = selected.primary
            palm_facing = (
                is_palm_facing_thumb_pinky(active_hand, mirrored_input=config.tracker.mirror_input)
                if active_hand is not None
                else False
            )
            movement_enabled = active_hand is not None and palm_facing
            anchor_norm = _movement_anchor_norm(active_hand) if active_hand is not None else None

            actions, movement_status = controller.update(
                anchor_norm=anchor_norm,
                movement_enabled=movement_enabled,
                now=time.time(),
            )
            execute_actions(actions)

            debug_frame = frame_bgr.copy()
            _draw_mouse_smoke(
                debug_frame,
                vision=vision,
                tracker=tracker,
                selector=selector,
                mirrored_input=config.tracker.mirror_input,
                movement_status=movement_status,
                movement_enabled=movement_enabled,
            )

            cv2.imshow(window_name, debug_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

        cv2.destroyAllWindows()

from __future__ import annotations

from bootstrap import ensure_repo_root_on_path
from common import PlainTestSuite
from fixtures import make_hand

ensure_repo_root_on_path()

from hand_controller.gestures.mouse_clicks import MouseClickDetector


FRAME_WIDTH = 1000
FRAME_HEIGHT = 1000


def run() -> object:
    suite = PlainTestSuite("Mouse Click Detector")

    left_pinch_hand = make_hand(overrides={4: (0.50, 0.50, 0.0), 8: (0.51, 0.50, 0.0), 12: (0.60, 0.50, 0.0)})
    released_hand = make_hand(overrides={4: (0.50, 0.50, 0.0), 8: (0.70, 0.50, 0.0), 12: (0.70, 0.50, 0.0)})
    right_pinch_hand = make_hand(overrides={4: (0.50, 0.50, 0.0), 8: (0.70, 0.50, 0.0), 12: (0.51, 0.50, 0.0)})

    detector = MouseClickDetector()
    first = detector.analyze(active_hand=left_pinch_hand, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT)
    suite.check_true("left pinch enters pressed state", first.left_pressed)
    suite.check_true("left pinch triggers down event once", first.left_down)

    second = detector.analyze(active_hand=left_pinch_hand, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT)
    suite.check_true("holding the pinch keeps left_pressed true", second.left_pressed)
    suite.check_false("holding the same pinch does not retrigger left_down", second.left_down)

    released = detector.analyze(active_hand=released_hand, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT)
    suite.check_true("releasing the pinch triggers left_up", released.left_up)
    suite.check_false("released hand clears left_pressed", released.left_pressed)

    detector = MouseClickDetector()
    right = detector.analyze(active_hand=right_pinch_hand, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT)
    suite.check_true("right pinch enters pressed state", right.right_pressed)
    suite.check_true("right pinch triggers down event", right.right_down)

    detector = MouseClickDetector()
    blocked = detector.analyze(
        active_hand=left_pinch_hand,
        frame_width=FRAME_WIDTH,
        frame_height=FRAME_HEIGHT,
        activation_allowed=False,
    )
    suite.check_false("blocked gesture does not report left_pressed", blocked.left_pressed)
    blocked_still_pinched = detector.analyze(
        active_hand=left_pinch_hand,
        frame_width=FRAME_WIDTH,
        frame_height=FRAME_HEIGHT,
        activation_allowed=True,
    )
    suite.check_false("blocked state remains locked until release", blocked_still_pinched.left_down)
    detector.analyze(active_hand=released_hand, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT, activation_allowed=True)
    unblocked = detector.analyze(active_hand=left_pinch_hand, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT, activation_allowed=True)
    suite.check_true("after release, the next pinch can trigger again", unblocked.left_down)

    return suite.summary()


if __name__ == "__main__":
    run()

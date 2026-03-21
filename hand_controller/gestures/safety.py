from __future__ import annotations

from ..vision.models import DetectedHand


def is_palm_facing_thumb_pinky(hand: DetectedHand, *, mirrored_input: bool) -> bool:
    """Detect palm-facing using thumb/pinky x ordering.

    The rule depends on whether the camera frame is mirrored before processing.
    With mirrored input, the x-axis behaves like a selfie preview.
    """

    thumb_x = hand.landmark(4).x
    pinky_x = hand.landmark(20).x
    label = hand.label.lower()

    if mirrored_input:
        if label == "right":
            return thumb_x < pinky_x
        return thumb_x > pinky_x

    if label == "right":
        return thumb_x > pinky_x
    return thumb_x < pinky_x

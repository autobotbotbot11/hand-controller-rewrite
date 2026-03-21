# Gesture Spec v1

This document freezes the meaning of each gesture before implementation starts.

## System states
- `control_enabled`: when `False`, recognition still runs, but control actions are blocked.
- `mode`: `mouse` or `keyboard`.
- `movement_enabled`: mouse movement is allowed only when all required gates pass.

## MLP classes

### `idle`
- Meaning: valid MLP class with no action.
- Purpose: separate command gestures from non-command poses.
- Important note: open palm and other normal poses may belong to this class.
- Runtime action: none.

### `hold`
- Physical pose: closed fist.
- Runtime meaning: clutch.
- Runtime action: mouse movement off and mouse clicking off.
- Important note: this acts as a safety lock while the fist is active.
- Removed meaning: this no longer triggers Alt+Tab.

### `toggle`
- Physical pose: L-shape hand pose.
- Runtime meaning: toggle `control_enabled`.
- Runtime action: turn control on or off.
- Important note: camera, MediaPipe, and MLP inference stay running even when control is off so the user can turn control back on with the same gesture.
- Safety note: the pose must be sustained for the configured hold time before toggling.

### `undo`
- Physical pose: two-finger pose from the original MLP dataset.
- Runtime action: `Ctrl+Z`.
- Scope for v1: mouse mode only.

### `redo`
- Physical pose: second two-finger pose from the original MLP dataset.
- Runtime action: `Ctrl+Y`.
- Scope for v1: mouse mode only.

### Ignored MLP labels
- `left_click`
- `right_click`

These labels may still be predicted by the existing model, but they will not drive behavior in the rewrite because clicking is rule-based.

## Rule-based gestures

### Palm facing
- Used as a safety gate for mouse control.
- If palm is not facing the camera, mouse movement is disabled.

### Left click
- Physical pose: thumb-index pinch.
- Runtime action: quick pinch-and-release = single left click.

### Double click
- Meaning: two quick left tap cycles within the configured interval.
- Runtime action: first click happens on the first release, and the second click may fire as the second pinch begins so the OS interprets them as a double click more easily.

### Right click
- Physical pose: thumb-middle pinch.
- Runtime action: pinch down = single right click.

### Drag
- Physical pose: thumb-index pinch held longer than the drag threshold.
- Runtime action: start left-button hold and allow drag movement.
- Release action: releasing the pinch ends the drag.

### Keyboard toggle
- Physical pose: thumb-ring pinch.
- Runtime action: toggle `mode` between `mouse` and `keyboard`.
- This replaces the two-hand keyboard activation logic from codebase 2.

### Keyboard input
- Keyboard mode uses the cleaner codebase 1 behavior:
  - pointer hovers over a key
  - thumb-index pinch confirms a key press
  - thumb-middle pinch sends backspace
  - thumb-pinky pinch arms one-shot shift for the next letter key press

## Mouse mode rules
- Mouse mode only produces actions when `control_enabled` is `True`.
- Mouse movement requires:
  - `control_enabled == True`
  - `mode == mouse`
  - palm-facing gate passes
  - `hold` is not active
- Clicking is blocked while `hold` is active.
- During a left pinch, movement freezes only until drag starts.
- During a right pinch, movement stays frozen until the pinch is released.
- `undo` and `redo` are ML-owned one-shot commands in mouse mode.

## Keyboard mode rules
- Keyboard toggle is rule-based.
- Keyboard interaction logic comes from the codebase 1 design, not from the codebase 2 two-hand idle logic.
- `hold` has no special meaning in keyboard mode for v1.
- `undo` and `redo` are ignored in keyboard mode for v1.

## Removed or rejected behaviors
- No Alt+Tab action from `hold`.
- No two-hand idle keyboard activation.
- No ML-owned click behavior.
- No dependency on `idle` for movement semantics.

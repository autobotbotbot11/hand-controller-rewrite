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
- Runtime action: mouse movement off only.
- Important note: clicking remains allowed while `hold` is active.
- Removed meaning: this no longer triggers Alt+Tab.

### `toggle`
- Physical pose: L-shape hand pose.
- Runtime meaning: toggle `control_enabled`.
- Runtime action: turn control on or off.
- Important note: camera, MediaPipe, and MLP inference stay running even when control is off so the user can turn control back on with the same gesture.

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
- Runtime action: single left click.

### Double click
- Meaning: two left-click pinches within the configured interval.
- Runtime action: double left click.

### Right click
- Physical pose: thumb-middle pinch.
- Runtime action: single right click.

### Keyboard toggle
- Physical pose: thumb-ring pinch.
- Runtime action: toggle `mode` between `mouse` and `keyboard`.
- This replaces the two-hand keyboard activation logic from codebase 2.

### Keyboard input
- Keyboard mode uses the cleaner codebase 1 behavior:
  - pointer hovers over a key
  - thumb-index pinch confirms a key press

## Mouse mode rules
- Mouse mode only produces actions when `control_enabled` is `True`.
- Mouse movement requires:
  - `control_enabled == True`
  - `mode == mouse`
  - palm-facing gate passes
  - `hold` is not active
- Clicking stays allowed while `hold` is active.
- Movement should also freeze during active click pinch to improve precision when targeting on-screen items.

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

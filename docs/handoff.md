# Handoff Notes

This file is the fastest way for a future AI or collaborator to understand the rewrite without relying on old chat history.

## Project summary

This project is a clean rewrite of a hand-based mouse and keyboard controller using:
- MediaPipe for hand tracking
- an existing MLP model for a small set of high-level gestures
- rule-based logic for precise click behavior and keyboard behavior

The rewrite exists because the original project split into two codebases with conflicting designs:
- `C:\Users\acer\school\self-study\programming\projects\computer-vision-mouse-control\hand_controller`
  - organized architecture
  - good clicking
  - keyboard flow is better
  - mouse movement is unstable
- `C:\Users\acer\school\self-study\programming\projects\computer-vision-mouse-control\touch-v15`
  - smooth mouse movement
  - working MLP artifacts
  - messy runtime semantics and confusing code

The rewrite must not merge those repos blindly. It should reuse ideas from both in a controlled, incremental way.

## Frozen decisions

These decisions are intentional and should not be changed casually.

### Control toggle
- ML `toggle` uses the L-shape pose.
- It toggles `control_enabled` only.
- It must not stop camera capture, MediaPipe, or MLP inference.
- Reason: the user must be able to turn control back on using the same gesture while the app is still running.

### Clutch
- ML `hold` uses the closed-fist pose.
- `hold` means clutch only.
- It disables mouse movement only.
- Clicking remains allowed while clutch is active.
- Reason: this improves precision because the cursor stops moving as the hand closes for a click.

### Idle
- `idle` is a real MLP class.
- It means no command action.
- It is not equivalent to "no hand detected".
- It may include open palm and other non-command poses.

### Click ownership
- Final behavior for mouse clicks is rule-based.
- `left click` = thumb-index pinch
- `double click` = two fast left pinches
- `right click` = thumb-middle pinch
- Existing MLP labels `left_click` and `right_click` may still be predicted, but they must not drive behavior in the rewrite.

### Keyboard
- Keyboard logic should follow the better design from `hand_controller`.
- Keyboard toggle is rule-based thumb-ring pinch.
- Do not use the two-hand idle keyboard activation logic from `touch-v15`.

### Undo / Redo
- Keep both in the rewrite.
- `undo` = `Ctrl+Z`
- `redo` = `Ctrl+Y`
- These are ML-owned commands.
- Recommended scope for v1: mouse mode only.

## Known physical MLP gesture poses

Based on user-provided labeled sample images:
- `hold` = closed fist
- `left_click` = thumb-index pinch
- `right_click` = thumb-middle pinch
- `toggle` = L-shape hand pose
- `undo` = side-oriented two-finger pose
- `redo` = front/upright two-finger pose
- `idle` = many non-command hand poses; it is a negative class, not absence of detection

## Why the rewrite is phased

The project should be built incrementally so every phase is testable before moving on.

The most important rule:
- do not add new complexity before the current layer is stable

Example:
- do not add clicking before mouse movement is stable
- do not add ML behavior before the base mouse controller is coherent
- do not add keyboard mode before mouse mode is solid

## Dependency baseline

Target runtime:
- Python 3.11

Pinned dependencies:
- `mediapipe==0.10.21`
- `scikit-learn==1.7.2`
- `PyQt5==5.15.11`
- `opencv-python==4.11.0.86`
- `numpy==2.2.3`
- `joblib==1.4.2`
- `pyautogui==0.9.54`
- `pillow==11.1.0`

Reason:
- this matches the practical compatibility target for MediaPipe and the existing saved MLP artifacts
- the existing model artifacts produced version mismatch warnings when loaded under a different `scikit-learn` version

## Current status

Completed:
- Phase 0: project contract
- Phase 1: package skeleton
- Phase 2 baseline code: camera wrapper, MediaPipe tracker wrapper, structured hand extraction, and a vision smoke runner
- Phase 2 validated on the user's machine: left and right hands are detected correctly
- Phase 3 baseline code: stable primary-hand selection with hysteresis and palm-facing safety detection
- Phase 3 validated on the user's machine
- Phase 4 baseline code: movement-only mouse controller, lazy action executor, and `--mouse-smoke`

Repo-local source of truth:
- `docs/gesture-spec.md`
- `docs/architecture.md`
- `docs/phase-plan.md`

Current package files:
- `hand_controller/app.py`
- `hand_controller/config/settings.py`
- `hand_controller/runtime/state.py`
- `hand_controller/ml/labels.py`

Smoke tests already passed:
- `python -m compileall hand_controller`
- `python -m hand_controller`
- import-level smoke test for the vision modules

## Next exact phase

Current validation task:
- install `requirements-phase4.txt`
- run `python -m hand_controller --mouse-smoke`
- confirm movement is stable and usable
- confirm movement stops when the active hand is not palm-facing
- confirm movement does not flicker badly when both hands are visible

Next implementation phase after validation:
- Phase 5: rule-based clicking

## Important warnings for future work

- Stable mouse movement is the top priority of the rewrite.
- Movement should adapt the useful algorithmic ideas from `touch-v15` without copying its full architecture.
- The rewrite should start synchronous and simple; add threading later only if it is truly needed.
- `hold` must not trigger Alt+Tab.
- `toggle` must not kill recognition.
- `idle` must not be used as the basis for movement semantics.
- Keyboard behavior should come from the cleaner `hand_controller` design.
- Clicking should stay rule-based even if the MLP predicts click labels.

## If another AI continues this work

Start by reading:
1. `docs/handoff.md`
2. `docs/gesture-spec.md`
3. `docs/architecture.md`
4. `docs/phase-plan.md`

Then continue only with the next unfinished phase instead of jumping ahead.

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
- It should require a short sustained hold before toggling.
- Reason: the user must be able to turn control back on using the same gesture while the app is still running.

### Clutch
- ML `hold` uses the closed-fist pose.
- `hold` means clutch only.
- It disables mouse movement and mouse clicks.
- Reason: in practice, the fist pose can accidentally collapse into thumb-index or thumb-middle contact, so click lock is safer.

### Idle
- `idle` is a real MLP class.
- It means no command action.
- It is not equivalent to "no hand detected".
- It may include open palm and other non-command poses.

### Click ownership
- Final behavior for mouse clicks is rule-based.
- `left click` = quick thumb-index pinch-and-release
- `double click` = first left tap releases normally, then the second click can fire as the second pinch begins
- `double_click_assist_window` limits how long that early second-click assist stays active so drag is less likely to be stolen
- `right click` = thumb-middle pinch down
- `drag` = thumb-index pinch held long enough to trigger left-button hold
- Existing MLP labels `left_click` and `right_click` may still be predicted, but they must not drive behavior in the rewrite.

### Keyboard
- Keyboard logic should follow the better design from `hand_controller`.
- Keyboard toggle is rule-based thumb-ring pinch.
- Do not use the two-hand idle keyboard activation logic from `touch-v15`.
- Keyboard mode includes:
  - thumb-index pinch to type hovered key
  - thumb-middle pinch for backspace
  - thumb-pinky pinch for one-shot Shift

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

Current phase-based install strategy:
- `requirements.txt`
  - `absl-py==2.4.0`
  - `attrs==26.1.0`
  - `flatbuffers==25.12.19`
  - `matplotlib==3.10.8`
  - `numpy==1.26.4`
  - `opencv-contrib-python==4.11.0.86`
  - `protobuf==4.25.8`
- `mediapipe==0.10.21 --no-deps`
- `requirements-phase4.txt`
  - `pyautogui==0.9.54`
  - `pillow==12.1.1`
- `requirements-later.txt`
  - heavier packages for ML and UI phases, including `scikit-learn==1.7.2`, `joblib`, and `PyQt5`
- `tuning.local.json`
  - optional repo-root JSON overrides that let the user tune click and movement behavior without editing Python code
- `tuning.recommended.json`
  - recommended preset for testing the current click/drag behavior without relying on whatever values are in `tuning.local.json`

Reason:
- this avoids pulling unnecessary heavy MediaPipe extras too early
- the MLP artifacts should still load later under `scikit-learn==1.7.2`

## Current status

Completed:
- Phase 0: project contract
- Phase 1: package skeleton
- Phase 2 baseline code: camera wrapper, MediaPipe tracker wrapper, structured hand extraction, and a vision smoke runner
- Phase 2 validated on the user's machine: left and right hands are detected correctly
- Phase 3 baseline code: stable primary-hand selection with hysteresis and palm-facing safety detection
- Phase 3 validated on the user's machine
- Phase 4 validated on the user's machine: stable mouse movement is smooth and usable
- Phase 5 click/drag refactor code: release-based left tap, easier double-click path, down-triggered right click, hold-to-drag, JSON tuning overrides, and updated `--mouse-smoke`
- Phase 6 baseline code: MLP predictor, action adapter, fallback artifact lookup to `touch-v15`, and integrated `toggle` / `hold` / `undo` / `redo` in `--mouse-smoke`
- Phase 8 baseline code: rule-based thumb-ring keyboard mode toggle, keyboard overlay, pinch-to-type keypresses, backspace gesture, one-shot Shift gesture, and integrated control smoke runner
- Phase K1 foundation code: `ui/main_window.py`, `ui/overlay_window.py`, `ui/signals.py`, typed overlay payloads, and `--ui-smoke` for validating the Qt overlay architecture
- Phase K2/K3 baseline code: `runtime/ui_live_control.py` and `--ui-live` now run the real CV worker through the Qt control panel + transparent overlay path
- Phase K4 baseline code: `controllers/keyboard_controller.py` now builds a data-driven full keyboard layout with a complete practical key set and configurable row/size/width settings
- Phase K6 cleanup code: `runtime/control_engine.py` now centralizes mouse mode, keyboard mode, ML updates, and transition cleanup so both `--control-smoke` and `--ui-live` share the same behavior
- Hardening baseline: local ML artifacts now exist in `artifacts/`, and `runtime/validation.py` provides a repo-local validation command
- Phase K7 config exposure: the Qt overlay now reads keyboard visual settings from `KeyboardConfig`, including selfie size, pointer radius, skeleton visibility, font sizes, and status panel sizing
- Keyboard redesign baseline: `controllers/keyboard_controller.py` now uses a 2-page model (`ABC` + `123/symbols`), fixes punctuation key output mappings, adds `Caps Lock`, and visibly changes alpha-page case for `Shift` / `Caps`
- Current Phase 6 behavior uses configurable ML settings under the `ml` section of the tuning JSON files.

Repo-local source of truth:
- `docs/gesture-spec.md`
- `docs/architecture.md`
- `docs/phase-plan.md`
- `docs/keyboard-v1-design.md`
- `docs/keyboard-v1-implementation-plan.md`
- `docs/group-testing.md`

Current package files:
- `hand_controller/app.py`
- `hand_controller/config/settings.py`
- `hand_controller/runtime/state.py`
- `hand_controller/runtime/control_engine.py`
- `hand_controller/runtime/validation.py`
- `hand_controller/ml/labels.py`
- `hand_controller/ui/overlay_window.py`
- `hand_controller/controllers/keyboard_controller.py`
- `hand_controller/controllers/mode_toggle.py`
- `hand_controller/gestures/hand_pinches.py`
- `hand_controller/ui/main_window.py`
- `hand_controller/ui/overlay_window.py`
- `hand_controller/ui/payloads.py`
- `hand_controller/ui/signals.py`
- `hand_controller/runtime/ui_foundation_smoke.py`
- `hand_controller/runtime/ui_live_control.py`

Tester-friendly repo entrypoints:
- `requirements-app.txt`
- `tuning.testing.json`
- `setup-tester.ps1`
- `run-tester.ps1`
- `docs/group-testing.md`

Smoke tests already passed:
- `python -m compileall hand_controller`
- `python -m hand_controller`
- import-level smoke test for the vision modules

## Next exact phase

Current validation task:
- run `python -m hand_controller --validate`
- confirm the rewrite resolves ML artifacts from `hand-controller-rewrite/artifacts/`
- confirm the validator reports `ml_uses_local_artifacts=True`
- run `python -m hand_controller --ui-live --tuning .\\tuning.local.json`
- confirm keyboard visual tuning now responds to JSON config changes without Python edits
- install `requirements-later.txt` if PyQt5 is not present yet
- run `python -m hand_controller --ui-smoke`
- confirm the control panel window opens
- click Start and confirm the transparent fullscreen overlay opens
- confirm Stop closes the overlay cleanly
- confirm closing the control panel also shuts down the overlay/worker cleanly
- confirm the overlay can render mock keyboard rectangles, pointers, and skeleton lines
- run `python -m hand_controller --ui-live --tuning .\\tuning.local.json`
- confirm the real camera/MediaPipe loop starts from the control panel window
- confirm mouse mode still works while using the Qt overlay path
- confirm keyboard mode renders the full data-driven keyboard on the transparent overlay instead of the OpenCV window
- confirm live skeleton lines, pointer markers, selfie preview, and status text appear on the overlay
- confirm the full practical key set is present and usable on the overlay
- confirm layout sizing and spacing remain sensible on the user's display
- confirm mouse <-> keyboard transitions feel stable in both `--control-smoke` and `--ui-live`
- confirm switching modes does not leave stale drag/click state behind
- confirm punctuation keys now produce output
- confirm the `ABC` / `123` page switch feels usable
- confirm `ESC` sits beside `Q` and `TAB` sits beside `A` on the `ABC` page
- confirm `Shift` visibly changes the alpha page
- confirm `Caps Lock` visibly changes the alpha page and behaves predictably
- install `requirements-later.txt` if ML dependencies are not present yet
- run `python -m hand_controller --control-smoke`
- confirm left click via quick thumb-index pinch-and-release
- confirm right click via thumb-middle pinch down
- confirm two quick left tap cycles feel easier than before
- confirm left-hold starts drag and releasing the pinch ends drag
- confirm cursor freezes before drag starts, not for the entire drag
- adjust `tuning.local.json` if the click feel still needs experimentation
- confirm `toggle` can turn control off and on again while the preview keeps running
- confirm `toggle` requires a short sustained hold before firing
- confirm `hold` freezes movement and blocks clicks
- confirm `undo` and `redo` hotkeys fire once per gesture
- confirm thumb-ring hold toggles into keyboard mode and back to mouse mode
- confirm thumb-index pinch types the hovered key in keyboard mode
- confirm thumb-middle pinch sends backspace in keyboard mode
- confirm thumb-pinky pinch arms one-shot Shift for the next letter key press

Next implementation phase after validation:
- Phase K8: focused keyboard-flaw validation/refinement pass

## Important warnings for future work

- Stable mouse movement is the top priority of the rewrite.
- Movement should adapt the useful algorithmic ideas from `touch-v15` without copying its full architecture.
- The rewrite should start synchronous and simple; add threading later only if it is truly needed.
- Prefer the rewrite repo's local `artifacts/` directory as the primary ML source.
- `hold` must not trigger Alt+Tab.
- `toggle` must not kill recognition.
- `idle` must not be used as the basis for movement semantics.
- Keyboard behavior should come from the cleaner `hand_controller` design.
- `hold`, `undo`, and `redo` should stay inactive while in keyboard mode.
- Clicking should stay rule-based even if the MLP predicts click labels.

## If another AI continues this work

Start by reading:
1. `docs/handoff.md`
2. `docs/gesture-spec.md`
3. `docs/architecture.md`
4. `docs/phase-plan.md`

Then continue only with the next unfinished phase instead of jumping ahead.

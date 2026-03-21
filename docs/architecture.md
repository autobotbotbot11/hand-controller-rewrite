# Architecture Contract v1

This rewrite keeps the code modular and intentionally separates perception, decision, and side effects.

## Module layout
- `hand_controller/app.py`
  - top-level entry point
- `hand_controller/config/`
  - frozen settings and tunable defaults
- `hand_controller/vision/`
  - camera access, MediaPipe hand tracking, stable active-hand selection
- `hand_controller/ml/`
  - model loading, label normalization, and MLP adapter
- `hand_controller/gestures/`
  - rule-based gesture utilities
- `hand_controller/controllers/`
  - mouse controller, keyboard controller, control-state controller
- `hand_controller/runtime/`
  - runtime state and the frame-by-frame orchestration loop
- `hand_controller/ui/`
  - control panel, overlay, and preview windows

## Design boundaries
- Vision modules return structured hand data only.
- The MLP adapter returns labels and confidence only.
- Controllers decide what should happen.
- The action executor is the only layer allowed to call `pyautogui`.
- UI reads state and displays it; it does not own control logic.

## Rewrite principles
- Start from a frozen contract before adding behavior.
- Build one layer at a time.
- Test each phase before moving forward.
- Prefer simple synchronous runtime flow first.
- Add threading only if profiling shows it is needed later.

## Mouse movement strategy
Stable movement will adapt the useful parts of codebase 2 without copying its entire runtime structure.

Key ideas to port:
- stable active-hand selection with hysteresis
- movement anchor at index MCP instead of fingertip or wrist
- relative movement instead of absolute hand-to-screen mapping
- anti-jitter wake and sleep thresholds
- spike clamp and per-frame step cap
- re-anchor logic after large discontinuities
- fast action execution with no extra per-action pause

## Control model
- `control_enabled` is toggled by the MLP `toggle` gesture.
- Recognition continues even when control is disabled.
- `mode` is toggled by rule-based thumb-ring pinch.
- Mouse clicks remain rule-based.
- `hold` is mapped to clutch, not Alt+Tab.

## Initial scope
- Mouse mode
- Keyboard mode
- Control toggle
- Clutch
- Undo / redo
- Minimal UI with room for later tuning controls

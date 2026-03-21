# Phase Plan

Each phase must have a real smoke test before the next phase starts.

## Phase 0: Project Contract
- Freeze gesture meanings.
- Freeze state model.
- Freeze dependency baseline.

Exit criteria:
- No ambiguous gesture semantics remain.

## Phase 1: Skeleton Setup
- Create package layout.
- Add entry points and baseline config modules.

Exit criteria:
- `python -m hand_controller` runs successfully.

## Phase 2: Vision Baseline
- Camera access.
- MediaPipe hand detection.
- Hand extraction and handedness.

Exit criteria:
- The app can show reliable hand presence and handedness.

## Phase 3: Hand Selection and Safety Gates
- Stable active-hand selection.
- Palm-facing detection.

Exit criteria:
- The controlling hand is stable and predictable.

## Phase 4: Stable Mouse Movement
- Relative movement.
- Anti-jitter filtering.
- Re-anchor logic.
- Movement tuning defaults.

Exit criteria:
- Cursor movement is smooth and usable.

## Phase 5: Rule-Based Clicking
- Left click.
- Double click.
- Right click.
- Movement freeze during active click pinch.

Exit criteria:
- Clicking is reliable and targeting is precise.

## Phase 6: MLP Adapter
- Load existing artifacts.
- Honor `toggle`, `hold`, `undo`, `redo`.
- Ignore MLP click labels for behavior.

Exit criteria:
- MLP commands work without breaking movement or clicks.

## Phase 7: Control-State Manager
- Formalize `control_enabled`.
- Block actions when control is off.
- Keep recognition alive when control is off.

Exit criteria:
- The user can turn control off and back on from the camera.

## Phase 8: Keyboard Mode
- Rule-based keyboard toggle.
- Keyboard overlay and key input logic.

Exit criteria:
- Keyboard mode is usable with one hand.

## Phase 9: UI
- Start / stop.
- Status.
- Mode.
- Control enabled / disabled.
- Optional preview and overlay.

Exit criteria:
- The app is usable without the terminal.

## Phase 10: Tuning and Validation
- Threshold tuning.
- Real-use testing.
- False-positive reduction.

Exit criteria:
- Demo-ready behavior.

## Phase 11: Cleanup
- Naming cleanup.
- Comments.
- Setup documentation.

Exit criteria:
- Repo is ready for handoff and presentation.

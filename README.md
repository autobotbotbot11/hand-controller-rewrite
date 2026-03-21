# Hand Controller Rewrite

Clean rewrite of the hand-based mouse and keyboard controller.

This repo intentionally starts from a frozen contract instead of merging the two older codebases directly.

Current status:
- Phase 0 complete: gesture contract and architecture contract are frozen.
- Phase 1 complete: minimal runnable package skeleton exists.
- Phase 2 complete: camera wrapper, MediaPipe hand tracker, structured hand output, and a validated vision smoke runner.
- Confirmed locally by the user: left and right hands are both detected.
- Phase 3 complete: active-hand selection and palm-facing safety detection passed local validation.
- Phase 4 complete: stable mouse movement passed local validation on the user's machine.
- Phase 5 click/drag refactor code exists: tap-based left click, easier double-click behavior, down-triggered right click, hold-to-drag, and a JSON tuning override file.
- Phase 6 baseline code exists: MLP adapter for `toggle`, `hold`, `undo`, and `redo`, with artifact fallback to the existing `touch-v15` model files.
- Phase 8 baseline code exists: rule-based thumb-ring keyboard toggle, keyboard overlay, pinch-to-type key input, middle-pinch backspace, and pinky-pinch one-shot shift.
- Phase K1 foundation code exists: control panel window, transparent overlay window, signal bus, and a dedicated `--ui-smoke` architecture test path.
- Phase K2/K3 baseline code exists: `--ui-live` runs the real CV worker and emits live keyboard, skeleton, selfie, and status payloads into the transparent Qt overlay.
- Phase K4 baseline code exists: the keyboard layout is now data-driven, uses a complete practical key set, and supports configurable sizing, spacing, bottom margin, row definitions, and per-key width units.
- Phase K6 cleanup code exists: mouse mode, keyboard mode, ML gating, and transition handling now flow through one shared live-control engine used by both `--control-smoke` and `--ui-live`.

## Baseline
- Python 3.11
- MediaPipe for hand tracking
- Existing MLP artifacts can be reused later through an adapter layer
- Mouse clicks remain rule-based

## First principles for this rewrite
- Stable mouse movement is the highest priority.
- Clicking must stay accurate and predictable.
- The MLP only owns a small set of high-level commands.
- The keyboard flow will follow the cleaner design from codebase 1.
- Keyboard thresholds and mode-toggle timing should stay JSON-configurable.
- Every phase must be testable before moving to the next one.

## Docs
- `docs/gesture-spec.md`
- `docs/architecture.md`
- `docs/phase-plan.md`
- `docs/keyboard-v1-design.md`
- `docs/keyboard-v1-implementation-plan.md`

## Setup
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
pip install mediapipe==0.10.21 --no-deps
python -m hand_controller
```

The app automatically loads `tuning.local.json` from the repo root if it exists.
Edit that file to experiment with click thresholds and timing without changing Python code.
If you want a clean known-good starting point, use `tuning.recommended.json`.

If disk space is too tight for a fresh rewrite venv, you can temporarily reuse
an existing project venv that already has the stack installed. For example:

```powershell
& 'C:\Users\acer\school\self-study\programming\projects\computer-vision-mouse-control\touch-v15\.venv\Scripts\python.exe' -m hand_controller
```

## Phase 2 smoke run
```powershell
python -m hand_controller --vision-smoke
```

Press `q` to close the OpenCV preview window.

## Phase K1 UI foundation smoke run
Install the later-phase desktop packages first:

```powershell
pip install -r requirements-later.txt
```

Then run:

```powershell
python -m hand_controller --ui-smoke
```

What it does:
- opens a normal control panel window
- opens a fullscreen transparent overlay on Start
- uses a worker thread plus Qt signal bus
- renders mock keyboard/skeleton/pointer payloads on the overlay
- validates clean Start / Stop / close lifecycle

This is the architecture validation step for the future final keyboard UI.
It is not yet the final live camera-driven overlay path.

## Phase K2/K3 live overlay run
Run the real control worker through the Qt control panel and transparent overlay:

```powershell
python -m hand_controller --ui-live --tuning .\tuning.local.json
```

What it does:
- opens the control panel window
- Start launches the real camera, MediaPipe, and controller worker
- renders the live full keyboard overlay on the transparent Qt overlay
- renders live skeleton lines, selfie preview, and status text on the same overlay
- keeps mouse actions active in mouse mode
- uses the Qt overlay instead of the OpenCV debug window for keyboard rendering
- uses a data-driven keyboard layout instead of the old simplified QWERTY-only keyboard
- uses the same shared control engine as `--control-smoke`, so mode transitions and ML/mouse/keyboard gating stay consistent

## Live Control Smoke Run
Install the extra packages for real cursor movement:

```powershell
pip install -r requirements-phase4.txt
```

Then run:

```powershell
python -m hand_controller --control-smoke
```

What it does:
- uses the active hand selected in Phase 3
- allows movement only when the active hand is palm-facing
- moves the real cursor using relative movement
- adds rule-based thumb-index left click and thumb-middle right click
- treats quick thumb-index pinch-and-release as a left click
- makes double click easier by allowing the second click to fire as the second pinch begins
- triggers right click on middle-pinch down instead of waiting for release
- supports hold-to-drag after the configured left-hold threshold
- freezes cursor only before drag starts, so targeting stays stable without blocking drag
- toggles keyboard mode with a held thumb-ring pinch on the active hand
- draws a virtual keyboard overlay in keyboard mode
- types the hovered key with thumb-index pinch
- sends backspace with thumb-middle pinch in keyboard mode
- arms one-shot Shift with thumb-pinky pinch in keyboard mode
- shows pinch-state debug info on the preview window

## Click Tuning
The easiest way to experiment is to edit `tuning.local.json` and rerun `--control-smoke`.

Most useful fields:
- `left_pinch_threshold_px`
- `right_pinch_threshold_px`
- `double_click_interval`
- `double_click_assist_window`
- `click_cooldown`
- `left_hold_drag_seconds`
- `left_press_multiplier`
- `left_release_multiplier`
- `right_press_multiplier`
- `right_release_multiplier`

Keyboard fields live under the `keyboard` section:
- `height_ratio`
- `side_margin_px`
- `bottom_margin_px`
- `key_gap_px`
- `row_gap_px`
- `layout_rows`
- `key_width_units`
- `index_pinch_threshold_px`
- `middle_pinch_threshold_px`
- `ring_pinch_threshold_px`
- `pinky_pinch_threshold_px`
- `mode_toggle_hold_seconds`
- `mode_toggle_cooldown_seconds`
- `require_palm_facing_for_toggle`

ML control fields live under the `ml` section:
- `confirm_frames`
- `toggle_hold_seconds`
- `toggle_cooldown`
- `shortcut_cooldown`
- `gate_min_p1`
- `gate_min_margin`

You can also point to another file explicitly:

```powershell
python -m hand_controller --control-smoke --tuning .\tuning.local.json
```

Recommended preset test:

```powershell
python -m hand_controller --control-smoke --tuning .\tuning.recommended.json
```

## Later-phase packages
When we reach ML integration and the desktop UI phases, install the heavier
packages separately:

```powershell
pip install -r requirements-later.txt
```

Phase 6 needs those later packages. If they are not installed yet, `--control-smoke`
will still run, but the ML overlay will show that ML is unavailable.

## Phase 6 ML behavior
When the ML artifacts and dependencies are available:
- `toggle` must be held briefly before it flips `control_enabled`
- `hold` freezes movement and disables rule-based clicks
- `undo` sends `Ctrl+Z`
- `redo` sends `Ctrl+Y`
- ignored MLP labels like `left_click` and `right_click` do not drive behavior

## Phase 8 keyboard behavior
- keyboard mode is toggled by a held thumb-ring pinch on the active hand
- keyboard mode remains one-hand usable
- `hold`, `undo`, and `redo` are ignored while in keyboard mode
- keyboard hit-testing uses fingertip positions mapped into the active keyboard layout space
- the live overlay keyboard now includes a complete practical key set:
  - `ESC`
  - digits `0-9`
  - letters `A-Z`
  - `TAB`
  - `BACKSPACE`
  - `ENTER`
  - `SHIFT`
  - `SPACE`
  - `;`
  - `'`
  - `,`
  - `.`
  - `/`
  - `\\`
  - `-`
  - `_`
  - `?`
  - `!`
  - `(`
  - `)`

Artifact lookup order:
1. `hand-controller-rewrite/artifacts/`
2. fallback to `touch-v15/hand_controller/artifacts/`

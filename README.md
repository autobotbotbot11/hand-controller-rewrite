# Hand Controller Rewrite

Clean rewrite of the hand-based mouse and keyboard controller.

This repo intentionally starts from a frozen contract instead of merging the two older codebases directly.

Current status:
- Phase 0 complete: gesture contract and architecture contract are frozen.
- Phase 1 complete: minimal runnable package skeleton exists.
- Phase 2 complete: camera wrapper, MediaPipe hand tracker, structured hand output, and a validated vision smoke runner.
- Confirmed locally by the user: left and right hands are both detected.
- Phase 3 complete: active-hand selection and palm-facing safety detection passed local validation.
- Phase 4 baseline code exists: stable movement-only mouse control and a dedicated mouse smoke runner.
- Live validation for Phase 4 is still needed on the user's machine.

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
- Every phase must be testable before moving to the next one.

## Docs
- `docs/gesture-spec.md`
- `docs/architecture.md`
- `docs/phase-plan.md`

## Setup
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
pip install mediapipe==0.10.21 --no-deps
python -m hand_controller
```

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

Phase 3 behavior now visible in that same smoke run:
- active controlling hand is highlighted
- palm-facing status is shown per hand
- top status line shows the selected active hand and its palm-facing gate

## Phase 4 mouse smoke run
Install the extra packages for real cursor movement:

```powershell
pip install -r requirements-phase4.txt
```

Then run:

```powershell
python -m hand_controller --mouse-smoke
```

What it does:
- uses the active hand selected in Phase 3
- allows movement only when the active hand is palm-facing
- moves the real cursor using relative movement
- draws the movement anchor on the preview window

## Later-phase packages
When we reach ML integration and the desktop UI phases, install the heavier
packages separately:

```powershell
pip install -r requirements-later.txt
```

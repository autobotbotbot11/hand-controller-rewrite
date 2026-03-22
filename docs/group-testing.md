# Group Testing Quick Guide

Use this guide if you only need to test the app and give feedback.

## Setup

Open PowerShell in the repo root and run:

```powershell
.\setup-tester.ps1
```

This will:
- create `.venv` if needed
- install the current app dependencies
- install `mediapipe==0.10.21` with the repo's tested setup

## Run the app

```powershell
.\run-tester.ps1
```

This starts the current live app path:
- control panel window
- transparent overlay
- mouse mode
- keyboard mode
- ML `toggle`, `hold`, `undo`, `redo`

It uses:
- `tuning.testing.json`

## What to test

- app start and stop
- mouse movement smoothness
- left click
- right click
- double click
- drag and drop
- ML `toggle` on/off
- ML `hold`
- `undo` / `redo`
- keyboard mode switch
- typing on the `ABC` page
- switching to the `123/symbols` page
- `Shift`
- `Caps Lock`
- `Backspace`
- `Space`
- `Enter`
- `ESC`
- `TAB`

## Feedback format

Use simple notes like this:

- mouse movement: good / bad
- left click: good / bad
- right click: good / bad
- double click: good / bad
- drag and drop: good / bad
- ML toggle: good / bad
- ML hold: good / bad
- keyboard typing: good / bad
- keys with no output: list them
- confusing behavior: describe it briefly

## If setup fails

- make sure Python 3.11 is installed
- close other apps using the camera
- run `python -m hand_controller --validate` inside `.venv` if needed

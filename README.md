# Hand Controller

Hand-tracking mouse and keyboard controller ito na gumagamit ng:
- MediaPipe for hand tracking
- rule-based mouse at keyboard interaction
- MLP para sa high-level commands (`toggle`, `hold`, `undo`, `redo`)

## Ano Ang Gumagana Ngayon
- mouse movement
- left click, right click, double click
- drag and drop
- ML `toggle`, `hold`, `undo`, `redo`
- keyboard mode with transparent overlay
- 2-page keyboard (`ABC` + `123/symbols`)
- `Shift`, `Caps Lock`, `Backspace`, `Space`, `Enter`, `ESC`, `TAB`

## Quick Start Para Sa Testers
Kung ite-test mo lang ang current app, ito lang ang gawin:

```powershell
.\setup-tester.ps1
.\run-tester.ps1
```

Ito ang gagamitin ng tester flow:
- [requirements.txt](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/requirements.txt)
- [tuning.testing.json](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/tuning.testing.json)

Tester guide:
- [group-testing.md](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/docs/group-testing.md)

## Manual Setup
Python 3.11 ang gamitin.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
pip install mediapipe==0.10.21 --no-deps
```

## Recommended Run
```powershell
python -m hand_controller --validate
python -m hand_controller --ui-live --tuning .\tuning.testing.json
```

`--ui-live` ang main app path:
- control panel window
- transparent overlay
- mouse mode
- keyboard mode
- live hand tracking

## Main Controls

### Mouse Mode
- move: active hand, palm facing sa camera
- left click: thumb + index pinch
- right click: thumb + middle pinch
- double click: two quick left-click pinches
- drag: hold the left pinch
- ML `hold`: hihinto ang movement at clicks for safety
- ML `toggle`: on/off ng control without stopping recognition
- ML `undo`: `Ctrl+Z`
- ML `redo`: `Ctrl+Y`

### Keyboard Mode
- mode switch: hold thumb + ring pinch
- press key: i-hover ang key, then thumb + index pinch
- backspace: thumb + middle pinch
- `ABC` / `123`: lipat ng keyboard page
- makikita ang `Shift` at `Caps Lock` state sa overlay

## Tuning Files
- [tuning.testing.json](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/tuning.testing.json)
  Shared baseline para sa group testing
- [tuning.local.json](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/tuning.local.json)
  Personal local adjustments
- [tuning.recommended.json](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/tuning.recommended.json)
  Optional reference preset

## Ibang Useful Commands
```powershell
python -m hand_controller --ui-smoke
python -m hand_controller --control-smoke --tuning .\tuning.local.json
python -m hand_controller --vision-smoke
python -m hand_controller --validate
```

## Project Docs
- [group-testing.md](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/docs/group-testing.md)
- [handoff.md](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/docs/handoff.md)
- [architecture.md](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/docs/architecture.md)
- [gesture-spec.md](/C:/Users/acer/school/self-study/programming/projects/computer-vision-mouse-control/hand-controller-rewrite/docs/gesture-spec.md)

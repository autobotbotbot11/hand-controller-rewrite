from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..config.settings import KeyboardConfig
from ..gestures.hand_pinches import HandPinchState
from ..vision.models import DetectedHand
from .actions import Action, Hotkey, KeyPress


INDEX_TIP_IDX = 8


@dataclass(frozen=True, slots=True)
class KeyboardKeySpec:
    token: str
    label: str
    action_kind: str
    action_value: str | tuple[str, ...] | None
    width_units: float = 1.0
    shift_action_kind: str | None = None
    shift_action_value: str | tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class KeyboardKeyRect:
    token: str
    label: str
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass(frozen=True, slots=True)
class KeyboardPointer:
    x: int
    y: int
    hand_label: str


@dataclass(slots=True)
class KeyboardState:
    shift_one_shot: bool = False


@dataclass(frozen=True, slots=True)
class KeyboardUpdate:
    actions: tuple[Action, ...] = ()
    layout: tuple[KeyboardKeyRect, ...] = ()
    highlight_labels: frozenset[str] = frozenset()
    pointers: tuple[KeyboardPointer, ...] = ()
    hovered_key_by_hand: tuple[tuple[str, str | None], ...] = ()
    shift_armed: bool = False
    status: str = "keyboard idle"


def _build_default_specs() -> dict[str, KeyboardKeySpec]:
    specs: dict[str, KeyboardKeySpec] = {
        "ESC": KeyboardKeySpec("ESC", "ESC", "key", "esc", width_units=1.20),
        "TAB": KeyboardKeySpec("TAB", "TAB", "key", "tab", width_units=1.40),
        "BACKSPACE": KeyboardKeySpec("BACKSPACE", "BKSP", "key", "backspace", width_units=1.90),
        "ENTER": KeyboardKeySpec("ENTER", "ENTER", "key", "enter", width_units=1.80),
        "SHIFT": KeyboardKeySpec("SHIFT", "SHIFT", "shift_one_shot", None, width_units=1.80),
        "SPACE": KeyboardKeySpec("SPACE", "SPACE", "key", "space", width_units=4.60),
        "SEMICOLON": KeyboardKeySpec(
            "SEMICOLON",
            ";",
            "key",
            "semicolon",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "semicolon"),
        ),
        "APOSTROPHE": KeyboardKeySpec(
            "APOSTROPHE",
            "'",
            "key",
            "quote",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "quote"),
        ),
        "COMMA": KeyboardKeySpec(
            "COMMA",
            ",",
            "key",
            "comma",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "comma"),
        ),
        "PERIOD": KeyboardKeySpec(
            "PERIOD",
            ".",
            "key",
            "period",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "period"),
        ),
        "SLASH": KeyboardKeySpec(
            "SLASH",
            "/",
            "key",
            "slash",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "slash"),
        ),
        "BACKSLASH": KeyboardKeySpec(
            "BACKSLASH",
            "\\",
            "key",
            "backslash",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "backslash"),
        ),
        "MINUS": KeyboardKeySpec(
            "MINUS",
            "-",
            "key",
            "minus",
            shift_action_kind="hotkey",
            shift_action_value=("shift", "minus"),
        ),
        "UNDERSCORE": KeyboardKeySpec(
            "UNDERSCORE",
            "_",
            "hotkey",
            ("shift", "minus"),
        ),
        "QUESTION": KeyboardKeySpec(
            "QUESTION",
            "?",
            "hotkey",
            ("shift", "slash"),
        ),
        "EXCLAMATION": KeyboardKeySpec(
            "EXCLAMATION",
            "!",
            "hotkey",
            ("shift", "1"),
        ),
        "LPAREN": KeyboardKeySpec(
            "LPAREN",
            "(",
            "hotkey",
            ("shift", "9"),
        ),
        "RPAREN": KeyboardKeySpec(
            "RPAREN",
            ")",
            "hotkey",
            ("shift", "0"),
        ),
    }

    shifted_digits = {
        "1": ("shift", "1"),
        "2": ("shift", "2"),
        "3": ("shift", "3"),
        "4": ("shift", "4"),
        "5": ("shift", "5"),
        "6": ("shift", "6"),
        "7": ("shift", "7"),
        "8": ("shift", "8"),
        "9": ("shift", "9"),
        "0": ("shift", "0"),
    }

    for digit in "1234567890":
        specs[digit] = KeyboardKeySpec(
            digit,
            digit,
            "key",
            digit,
            shift_action_kind="hotkey",
            shift_action_value=shifted_digits[digit],
        )

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        key_name = letter.lower()
        specs[letter] = KeyboardKeySpec(
            letter,
            letter,
            "key",
            key_name,
            shift_action_kind="hotkey",
            shift_action_value=("shift", key_name),
        )

    return specs


KEY_SPECS = _build_default_specs()


def _normalize_layout_rows(rows: Sequence[Sequence[str]] | Sequence[str]) -> tuple[tuple[str, ...], ...]:
    normalized_rows: list[tuple[str, ...]] = []
    for row in rows or ():
        if isinstance(row, str):
            tokens = tuple(part.strip().upper() for part in row.split() if part.strip())
        else:
            tokens = tuple(str(part).strip().upper() for part in row if str(part).strip())
        if tokens:
            normalized_rows.append(tokens)
    if not normalized_rows:
        raise ValueError("Keyboard layout must contain at least one non-empty row.")
    return tuple(normalized_rows)


def _resolve_width_units(settings: KeyboardConfig) -> dict[str, float]:
    resolved = {token: spec.width_units for token, spec in KEY_SPECS.items()}
    overrides = settings.key_width_units or {}
    if isinstance(overrides, Mapping):
        for token, width in overrides.items():
            resolved[str(token).strip().upper()] = float(width)
    return resolved


def _create_action(kind: str | None, value: str | tuple[str, ...] | None) -> Action | None:
    if kind is None or value is None:
        return None
    if kind == "key":
        return KeyPress(str(value))
    if kind == "hotkey":
        if isinstance(value, tuple):
            return Hotkey(value)
        if isinstance(value, list):
            return Hotkey(tuple(str(part) for part in value))
        raise ValueError(f"Hotkey action expects a tuple/list, got {type(value)!r}")
    raise ValueError(f"Unknown keyboard action kind: {kind}")


def create_keyboard_layout(
    frame_width: int,
    frame_height: int,
    settings: KeyboardConfig,
) -> tuple[KeyboardKeyRect, ...]:
    rows = _normalize_layout_rows(settings.layout_rows)
    width_units = _resolve_width_units(settings)

    for row in rows:
        for token in row:
            if token not in KEY_SPECS:
                raise ValueError(f"Unknown keyboard layout token: {token}")

    keyboard_height = int(frame_height * settings.height_ratio)
    keyboard_top = frame_height - keyboard_height - settings.bottom_margin_px
    keyboard_left = settings.side_margin_px
    keyboard_right = frame_width - settings.side_margin_px
    keyboard_width = max(1, keyboard_right - keyboard_left)
    gap_x = settings.key_gap_px
    gap_y = settings.row_gap_px

    unit_width = min(
        (keyboard_width - gap_x * max(0, len(row) - 1)) / max(1.0, sum(width_units[token] for token in row))
        for row in rows
    )
    row_height = (keyboard_height - gap_y * max(0, len(rows) - 1)) / len(rows)

    keys: list[KeyboardKeyRect] = []
    for row_index, row in enumerate(rows):
        y1 = int(round(keyboard_top + row_index * (row_height + gap_y)))
        y2 = int(round(y1 + row_height))

        row_width = sum(width_units[token] * unit_width for token in row) + gap_x * max(0, len(row) - 1)
        cursor_x = keyboard_left + (keyboard_width - row_width) / 2.0

        for token in row:
            spec = KEY_SPECS[token]
            width_px = max(1, int(round(width_units[token] * unit_width)))
            x1 = int(round(cursor_x))
            x2 = int(round(cursor_x + width_px))
            keys.append(
                KeyboardKeyRect(
                    token=token,
                    label=spec.label,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )
            cursor_x += width_px + gap_x

    return tuple(keys)


def get_key_at_point(keys: tuple[KeyboardKeyRect, ...], x: int, y: int) -> KeyboardKeyRect | None:
    for key in keys:
        if key.x1 <= x <= key.x2 and key.y1 <= y <= key.y2:
            return key
    return None


class KeyboardController:
    def __init__(self, settings: KeyboardConfig | None = None) -> None:
        self.settings = settings or KeyboardConfig()
        self.state = KeyboardState()
        self._layout_cache: tuple[int, int, tuple[KeyboardKeyRect, ...]] | None = None

    def reset(self) -> None:
        self.state.shift_one_shot = False

    def layout_for_frame(self, frame_width: int, frame_height: int) -> tuple[KeyboardKeyRect, ...]:
        cached = self._layout_cache
        if cached is not None and cached[0] == frame_width and cached[1] == frame_height:
            return cached[2]

        layout = create_keyboard_layout(frame_width, frame_height, self.settings)
        self._layout_cache = (frame_width, frame_height, layout)
        return layout

    def update(
        self,
        *,
        hands: tuple[DetectedHand, ...],
        pinch_states: dict[str, HandPinchState],
        frame_width: int,
        frame_height: int,
    ) -> KeyboardUpdate:
        layout = self.layout_for_frame(frame_width, frame_height)
        actions: list[Action] = []
        highlights: set[str] = set()
        pointers: list[KeyboardPointer] = []
        hovered_by_hand: dict[str, str | None] = {"Left": None, "Right": None}

        for pinch_state in pinch_states.values():
            if pinch_state.pinky.down:
                self.state.shift_one_shot = True
            if pinch_state.middle.down:
                actions.append(KeyPress("backspace"))

        for hand in hands:
            hand_label = hand.label
            tip = hand.landmark(INDEX_TIP_IDX)
            px = int(tip.x * frame_width)
            py = int(tip.y * frame_height)
            pointers.append(KeyboardPointer(x=px, y=py, hand_label=hand_label))

            key = get_key_at_point(layout, px, py)
            if key is None:
                continue

            hovered_by_hand[hand_label] = key.label
            highlights.add(key.label)
            pinch_state = pinch_states.get(hand_label)
            if pinch_state is None or not pinch_state.index.down:
                continue

            spec = KEY_SPECS[key.token]
            if spec.action_kind == "shift_one_shot":
                self.state.shift_one_shot = True
                continue

            if self.state.shift_one_shot and spec.shift_action_kind is not None:
                action = _create_action(spec.shift_action_kind, spec.shift_action_value)
            else:
                action = _create_action(spec.action_kind, spec.action_value)

            if action is not None:
                actions.append(action)
            self.state.shift_one_shot = False

        hovered_pairs = tuple(sorted(hovered_by_hand.items()))
        hovered_summary = " ".join(
            f"{hand}:{label or '-'}"
            for hand, label in hovered_pairs
        )
        status = f"keyboard shift={'on' if self.state.shift_one_shot else 'off'} hover={hovered_summary}"

        return KeyboardUpdate(
            actions=tuple(actions),
            layout=layout,
            highlight_labels=frozenset(highlights),
            pointers=tuple(pointers),
            hovered_key_by_hand=hovered_pairs,
            shift_armed=self.state.shift_one_shot,
            status=status,
        )

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Union


@dataclass(frozen=True, slots=True)
class MoveRelative:
    dx: int
    dy: int


@dataclass(frozen=True, slots=True)
class Click:
    button: Literal["left", "right"] = "left"


@dataclass(frozen=True, slots=True)
class DoubleClick:
    button: Literal["left"] = "left"


Action = Union[MoveRelative, Click, DoubleClick]

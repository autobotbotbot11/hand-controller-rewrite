from __future__ import annotations

from dataclasses import dataclass
import traceback


@dataclass(slots=True, frozen=True)
class SuiteResult:
    name: str
    passed: int
    failed: int

    @property
    def total(self) -> int:
        return self.passed + self.failed


class PlainTestSuite:
    def __init__(self, name: str) -> None:
        self.name = name
        self.passed = 0
        self.failed = 0

    def _record(self, ok: bool, title: str, detail: str = "") -> None:
        if ok:
            self.passed += 1
            print(f"PASS - {self.name} - {title}")
            return

        self.failed += 1
        suffix = f" | {detail}" if detail else ""
        print(f"FAIL - {self.name} - {title}{suffix}")

    def check_equal(self, title: str, actual, expected) -> None:
        self._record(
            actual == expected,
            title,
            detail=f"expected={expected!r}, actual={actual!r}",
        )

    def check_true(self, title: str, value) -> None:
        self._record(bool(value), title, detail=f"value={value!r}")

    def check_false(self, title: str, value) -> None:
        self._record(not bool(value), title, detail=f"value={value!r}")

    def check_close(self, title: str, actual: float, expected: float, tolerance: float = 1e-6) -> None:
        ok = abs(actual - expected) <= tolerance
        self._record(
            ok,
            title,
            detail=f"expected~={expected!r}, actual={actual!r}, tolerance={tolerance!r}",
        )

    def expect_exception(self, title: str, func, expected_exception: type[BaseException]) -> None:
        try:
            func()
        except expected_exception:
            self._record(True, title)
        except Exception as exc:  # pragma: no cover - diagnostic path
            self._record(
                False,
                title,
                detail=f"raised {type(exc).__name__} instead of {expected_exception.__name__}",
            )
        else:
            self._record(
                False,
                title,
                detail=f"expected {expected_exception.__name__} but nothing was raised",
            )

    def run_case(self, title: str, func) -> None:
        try:
            func()
        except Exception as exc:  # pragma: no cover - diagnostic path
            trace = traceback.format_exc(limit=2).replace("\n", " | ")
            self._record(False, title, detail=f"{type(exc).__name__}: {exc} | {trace}")

    def summary(self) -> SuiteResult:
        total = self.passed + self.failed
        print(f"SUMMARY - {self.name}: passed={self.passed}, failed={self.failed}, total={total}")
        print("-" * 72)
        return SuiteResult(name=self.name, passed=self.passed, failed=self.failed)

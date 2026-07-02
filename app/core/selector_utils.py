from __future__ import annotations

from typing import Iterable


def first_non_empty(values: Iterable[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None

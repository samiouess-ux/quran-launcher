"""Keep Quran ayahs whole and in their exact contiguous order."""
from __future__ import annotations
from collections.abc import Sequence
from typing import TypeVar
T = TypeVar("T")

def partition_contiguous_ayahs(ayahs: Sequence[T], durations_seconds: dict[int, float], maximum_seconds: float | None = None) -> tuple[list[list[T]], list[T]]:
    """Return whole-ayah parts capped by duration; leave overflow ayahs unselected."""
    if maximum_seconds is not None and maximum_seconds <= 0:
        raise ValueError("maximum_seconds must be positive.")
    numbers = [int(item["ayah"]) for item in ayahs]  # type: ignore[index]
    if not numbers:
        return [], []
    if len(numbers) != len(set(numbers)):
        raise ValueError("Requested ayahs contain duplicates.")
    if any(right != left + 1 for left, right in zip(numbers, numbers[1:])):
        raise ValueError("Requested ayahs must be one contiguous ordered range.")
    parts: list[list[T]] = []
    current: list[T] = []
    current_duration = 0.0
    for item, number in zip(ayahs, numbers):
        duration = float(durations_seconds[number])
        if duration <= 0:
            raise ValueError(f"Invalid processed duration for ayah {number}.")
        if maximum_seconds is not None and duration > maximum_seconds:
            break
        if maximum_seconds is not None and current and current_duration + duration > maximum_seconds:
            parts.append(current)
            current = []
            current_duration = 0.0
        current.append(item)
        current_duration += duration
    if current:
        parts.append(current)
    selected_count = sum(len(group) for group in parts)
    remaining = list(ayahs[selected_count:])
    flattened = [int(item["ayah"]) for group in parts for item in group]  # type: ignore[index]
    if flattened != numbers[:selected_count]:
        raise AssertionError("Ayah partition did not preserve the exact requested prefix.")
    return parts, remaining

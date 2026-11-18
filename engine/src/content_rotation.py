"""Deterministic content rotation with recent-repeat protection.

Only reviewed manifests are eligible. This module chooses existing files; it
never invents Quran verses, duas, translations, audio, or background assets.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


SUPPORTED_CONTENT_TYPES = {"quran", "dua", "dhikr"}


def choose_manifest(
    content_dir: Path,
    content_type: str,
    recent_ids: Iterable[str] = (),
    rotation_key: str = "",
) -> Path:
    if content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValueError("Unsupported content type.")
    recent = set(recent_ids)
    eligible: list[tuple[str, Path]] = []
    for path in sorted(content_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue

        # Treat malformed structures as ineligible data, never as a reason
        # to crash the rotation process or weaken the approval gate.
        if not isinstance(data, dict):
            continue
        publishing = data.get("publishing")
        if not isinstance(publishing, dict):
            continue
        # Every eligibility field must be explicit. Missing metadata is not
        # equivalent to user approval or a confirmed no-auto-publish setting.
        if data.get("content_type") != content_type:
            continue
        if data.get("rotation_approved") is not True:
            continue
        if publishing.get("approval_required") is not True:
            continue
        if publishing.get("auto_publish") is not False:
            continue

        item_id = data.get("id")
        if isinstance(item_id, str) and item_id.strip() and item_id not in recent:
            eligible.append((item_id, path))

    if not eligible:
        raise FileNotFoundError(
            f"No eligible non-recent {content_type} manifest; refusing to repeat or invent content."
        )
    digest = hashlib.sha256(rotation_key.encode("utf-8")).digest()
    return eligible[int.from_bytes(digest[:8], "big") % len(eligible)][1]


def choose_manifests(
    content_dir: Path,
    content_type: str,
    count: int,
    recent_ids: Iterable[str] = (),
    rotation_key: str = "",
) -> list[Path]:
    """Select a batch of distinct approved manifests or fail without a partial batch."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("count must be a positive integer.")
    recent = set(recent_ids)
    selected: list[Path] = []
    for index in range(count):
        try:
            candidate = choose_manifest(
                content_dir, content_type, recent_ids=recent,
                rotation_key=f"{rotation_key}:{index}",
            )
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Cannot build a complete batch of {count} distinct {content_type} manifests; "
                f"selected {len(selected)}. {exc}"
            ) from exc
        data = json.loads(candidate.read_text(encoding="utf-8"))
        recent.add(data["id"])
        selected.append(candidate)
    return selected

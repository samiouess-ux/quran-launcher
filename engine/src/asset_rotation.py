"""Choose only reviewed assets while avoiding recent repeats."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def choose_asset(catalog_path: Path, asset_kind: str, recent_ids: Iterable[str] = (),
                 rotation_key: str = "") -> dict:
    if asset_kind not in {"background", "audio"}:
        raise ValueError("asset_kind must be background or audio.")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.get(asset_kind, [])
    recent = set(recent_ids)
    eligible = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        asset_id = item.get("id")
        if not isinstance(asset_id, str) or not asset_id or asset_id in recent:
            continue
        if item.get("approved") is not True or item.get("user_approved") is not True:
            continue
        if item.get("rights_verified") is not True:
            continue
        if not str(item.get("source_url", "")).startswith("https://"):
            continue
        if not str(item.get("asset_url", "")).startswith("https://"):
            continue
        eligible.append(item)
    if not eligible:
        raise LookupError(
            f"No approved, rights-verified, non-recent {asset_kind} asset; refusing fallback."
        )
    digest = hashlib.sha256(rotation_key.encode("utf-8")).digest()
    return eligible[int.from_bytes(digest[:8], "big") % len(eligible)]

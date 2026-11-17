"""Select a small daily batch from reviewed manifests and approved assets.

This is a local selection step, not a publishing workflow. It updates history
only after a caller has successfully rendered and recorded the selected item.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from content_rotation import choose_manifest
from asset_rotation import choose_asset


def load_history(path: Path) -> dict:
    if not path.exists():
        return {"content": [], "background": [], "audio": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("History must be a JSON object.")
    return data


def select_batch(content_dir: Path, catalog: Path, history: dict, day_key: str) -> list[dict]:
    recent_content = history.get("content", [])
    recent_background = history.get("background", [])
    recent_audio = history.get("audio", [])
    selections = []
    for index, kind in enumerate(("quran", "dua", "dhikr")):
        manifest_path = choose_manifest(
            content_dir, kind, recent_content, f"{day_key}:{index}:{kind}"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        background = choose_asset(
            catalog, "background", recent_background,
            f"{day_key}:{index}:{kind}:background"
        )
        audio = choose_asset(
            catalog, "audio", recent_audio,
            f"{day_key}:{index}:{kind}:audio"
        )
        selections.append({
            "content_type": kind,
            "manifest": str(manifest_path),
            "content_id": manifest["id"],
            "background": background["id"],
            "audio": audio["id"],
        })
        recent_content = [*recent_content, manifest["id"]]
        recent_background = [*recent_background, background["id"]]
        recent_audio = [*recent_audio, audio["id"]]
    return selections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", default="content")
    parser.add_argument("--asset-catalog", default="content/assets_catalog.json")
    parser.add_argument("--history", default="content/rotation_history.json")
    parser.add_argument("--day", default=date.today().isoformat())
    args = parser.parse_args()
    history_path = Path(args.history)
    history = load_history(history_path)
    selected = select_batch(Path(args.content_dir), Path(args.asset_catalog), history, args.day)
    print(json.dumps({"day": args.day, "videos": selected}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""Select a reviewed manifest for the review-render workflow.

This is the production entry point for deterministic manifest rotation. It
only selects existing approved manifests and fails closed when none qualify.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from content_rotation import choose_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", default="content")
    parser.add_argument("--content-type", choices=("quran", "dua", "dhikr"), required=True)
    parser.add_argument("--recent-id", action="append", default=[])
    parser.add_argument("--rotation-key", required=True)
    args = parser.parse_args()

    try:
        selected = choose_manifest(
            Path(args.content_dir), args.content_type,
            recent_ids=args.recent_id, rotation_key=args.rotation_key,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Rotation stopped safely: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(selected.as_posix())


if __name__ == "__main__":
    main()

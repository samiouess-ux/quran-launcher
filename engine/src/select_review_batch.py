"""Select a complete batch of distinct reviewed manifests for manual review."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from content_rotation import choose_manifests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-dir", default="content")
    parser.add_argument("--content-type", choices=("quran", "dua", "dhikr"), required=True)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--recent-id", action="append", default=[])
    parser.add_argument("--rotation-key", required=True)
    args = parser.parse_args()

    try:
        selected = choose_manifests(
            Path(args.content_dir), args.content_type, args.count,
            recent_ids=args.recent_id, rotation_key=args.rotation_key,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Batch rotation stopped safely: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    for path in selected:
        print(path.as_posix())


if __name__ == "__main__":
    main()

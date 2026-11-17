"""Fail-closed exact Quran Arabic text validator.

The reference file is a reviewed, version-controlled snapshot for the selected
script/source. Comparisons are exact Unicode code-point comparisons: no
normalization, stripping, harakat removal, or substitutions are performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(manifest_path: Path, reference_path: Path) -> None:
    manifest = load_json(manifest_path)
    reference = load_json(reference_path)

    if reference.get("script") != "uthmani":
        raise SystemExit("Reference script must be explicitly declared as uthmani.")
    if not reference.get("source_url") or not reference.get("review_status") == "reviewed":
        raise SystemExit("Quran reference source/review metadata is missing.")

    source = manifest.get("source", {})
    chapter = source.get("surah_number")
    expected = reference.get("verses", {})
    verses = manifest.get("verses", [])
    if not verses:
        raise SystemExit("Manifest contains no verses.")

    requested = source.get("verses", [])
    if not isinstance(requested, list) or not requested:
        raise SystemExit("Manifest source.verses must list the requested verse numbers.")
    if len(requested) != len(set(requested)):
        raise SystemExit("Manifest source.verses contains duplicate verse numbers.")
    actual_numbers = [verse.get("number") for verse in verses]
    if actual_numbers != requested:
        raise SystemExit(
            "Manifest verse entries must exactly match source.verses in the same order."
        )

    seen = set()
    for verse in verses:
        number = verse.get("number")
        key = f"{chapter}:{number}"
        if key in seen:
            raise SystemExit(f"Duplicate verse key: {key}")
        seen.add(key)

        expected_text = expected.get(key)
        actual_text = verse.get("arabic")
        if not isinstance(expected_text, str) or not expected_text:
            raise SystemExit(f"Reference text missing for {key}; refusing to render.")
        if not isinstance(actual_text, str) or actual_text != expected_text:
            raise SystemExit(
                f"Quran text mismatch for {key}. Exact Unicode comparison failed; "
                "no automatic correction will be applied."
            )

    print(f"Quran Arabic validation passed: {len(verses)} verse(s), exact match.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument(
        "--reference",
        default="data/reference/quran_text_uthmani.json",
    )
    args = parser.parse_args()
    validate(Path(args.manifest), Path(args.reference))


if __name__ == "__main__":
    main()

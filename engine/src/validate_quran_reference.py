"""Validate the structure and coverage of the reviewed Quran reference snapshot.

This checks metadata and key integrity only. It cannot establish that a human
verified the Arabic strings against the cited source.
"""
import json
import re
import sys
from pathlib import Path


def validate_reference(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("script") != "uthmani":
        raise SystemExit("Reference script must be uthmani.")
    if data.get("review_status") != "reviewed":
        raise SystemExit("Reference snapshot is not marked reviewed.")
    if not isinstance(data.get("source_url"), str) or not data["source_url"].startswith("https://"):
        raise SystemExit("A trusted HTTPS source_url is required.")

    verses = data.get("verses")
    if not isinstance(verses, dict) or not verses:
        raise SystemExit("Reference verses must be a non-empty object.")

    for key, text in verses.items():
        if not re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", key):
            raise SystemExit(f"Invalid verse key: {key}")
        if not isinstance(text, str) or not text.strip():
            raise SystemExit(f"Missing Arabic text for {key}")
        # Do not normalize or modify the Quran string here.
    print(f"Reference structure passed: {len(verses)} reviewed verse(s).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python src/validate_quran_reference.py <reference.json>")
    validate_reference(Path(sys.argv[1]))

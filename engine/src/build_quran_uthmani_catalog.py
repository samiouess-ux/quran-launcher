"""Fetch the complete Uthmani Arabic Quran text as an UNREVIEWED candidate corpus.

The output is deliberately not accepted by the renderer's reviewed-reference
validator. Every verse must be independently checked before promotion.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

BASE = "https://api.alquran.cloud/v1"
EDITION = "quran-uthmani"
BASMALA_UTHMANI = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"
COUNTS = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "IslamicTikTokAutomation/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def validate_surah_payload(payload: dict, surah: int, expected_count: int) -> dict[str, str]:
    if not isinstance(payload, dict) or payload.get("code") != 200:
        raise ValueError(f"Surah {surah}: Uthmani API did not return HTTP 200 data")
    data = payload.get("data")
    ayahs = data.get("ayahs") if isinstance(data, dict) else None
    if not isinstance(ayahs, list):
        raise ValueError(f"Surah {surah}: missing ayahs array")
    verses: dict[str, str] = {}
    for item in ayahs:
        if not isinstance(item, dict):
            raise ValueError(f"Surah {surah}: malformed ayah row")
        number, text = item.get("numberInSurah"), item.get("text")
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= expected_count:
            raise ValueError(f"Surah {surah}: invalid ayah number {number!r}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Surah {surah}:{number}: empty Arabic text")
        key = f"{surah}:{number}"
        if key in verses:
            raise ValueError(f"Surah {surah}:{number}: duplicate Arabic text")
        # AlQuran Cloud prefixes the basmala to the first ayah of most
        # surahs. It is not part of that ayah (except Al-Fatihah); remove
        # only this exact known prefix for surahs 2-8 and 10-114.
        if number == 1 and surah not in (1, 9) and text.startswith(BASMALA_UTHMANI + " "):
            text = text[len(BASMALA_UTHMANI):].lstrip()
        verses[key] = text
    expected = {f"{surah}:{number}" for number in range(1, expected_count + 1)}
    if set(verses) != expected:
        missing = sorted(expected - set(verses))
        extra = sorted(set(verses) - expected)
        raise ValueError(f"Surah {surah}: incomplete Uthmani text; missing={missing[:5]}, extra={extra[:5]}")
    return verses


def build_catalog(fetcher=fetch_json) -> dict:
    if len(COUNTS) != 114 or sum(COUNTS) != 6236:
        raise ValueError("Internal canonical verse-count table is invalid")
    response = fetcher(f"{BASE}/quran/{EDITION}")
    if not isinstance(response, dict) or response.get("code") != 200:
        raise ValueError("Complete Uthmani API response did not return HTTP 200")
    data = response.get("data")
    surahs = data.get("surahs") if isinstance(data, dict) else None
    if not isinstance(surahs, list) or len(surahs) != 114:
        raise ValueError("Complete Uthmani response must contain all 114 surahs")
    verses: dict[str, str] = {}
    for surah, count in enumerate(COUNTS, 1):
        matching = [item for item in surahs if isinstance(item, dict) and item.get("number") == surah]
        if len(matching) != 1:
            raise ValueError(f"Complete Uthmani response has missing/duplicate surah {surah}")
        verses.update(validate_surah_payload({"code": 200, "data": matching[0]}, surah, count))
    if len(verses) != 6236:
        raise ValueError(f"Expected 6,236 Arabic verses, received {len(verses)}")
    return {
        "schema_version": 1,
        "source": "AlQuran Cloud API",
        "source_url": "https://api.alquran.cloud/v1/quran/quran-uthmani",
        "api_documentation": "https://alquran.cloud/api",
        "edition": EDITION,
        "script": "uthmani",
        "language": "ar",
        "expected_verse_count": 6236,
        "fetched_verse_count": len(verses),
        "review_status": "source_fetched_not_human_reviewed",
        "rendering_allowed": False,
        "review_note": "Automated completeness is not religious/editorial verification. Do not use as a renderer reference until exact text is independently checked and a reviewed snapshot is explicitly approved.",
        "unicode_policy": "Preserve source strings exactly; no normalization, stripping of marks, or substitutions.",
        "verses": dict(sorted(verses.items(), key=lambda pair: tuple(map(int, pair[0].split(":"))))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output/quran_uthmani_candidate.json"))
    args = parser.parse_args()
    catalog = build_catalog()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fetched {catalog['fetched_verse_count']} Uthmani Arabic verses from {catalog['edition']}; HUMAN REVIEW REQUIRED, rendering disabled.")


if __name__ == "__main__":
    main()

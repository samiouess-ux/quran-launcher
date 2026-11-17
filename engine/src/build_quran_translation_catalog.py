"""Fetch the complete Saheeh International ENGLISH translation from AlQuran Cloud.

The required video language is Arabic + English only; French is not part of this pipeline.

The translation text is preserved verbatim and every ayah is keyed by its
surah:ayah reference. Metadata and source attribution are embedded.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

BASE = "https://api.alquran.cloud/v1"
EDITION = "en.sahih"
COUNTS = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]


def fetch_json(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "IslamicTikTokAutomation/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def validate_surah_payload(payload: dict, surah: int, expected_count: int) -> dict[str, str]:
    if not isinstance(payload, dict) or payload.get("code") != 200:
        raise ValueError(f"Surah {surah}: translation API did not return HTTP 200 data")
    data = payload.get("data")
    ayahs = data.get("ayahs") if isinstance(data, dict) else None
    if not isinstance(ayahs, list):
        raise ValueError(f"Surah {surah}: missing ayahs array")
    translations: dict[str, str] = {}
    for item in ayahs:
        if not isinstance(item, dict):
            raise ValueError(f"Surah {surah}: malformed translation row")
        number = item.get("numberInSurah")
        text = item.get("text")
        if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= expected_count:
            raise ValueError(f"Surah {surah}: invalid ayah number {number!r}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Surah {surah}:{number}: empty translation")
        key = f"{surah}:{number}"
        if key in translations:
            raise ValueError(f"Surah {surah}:{number}: duplicate translation")
        translations[key] = text
    expected = {f"{surah}:{number}" for number in range(1, expected_count + 1)}
    if set(translations) != expected:
        missing = sorted(expected - set(translations))
        raise ValueError(f"Surah {surah}: incomplete translation; missing {missing[:10]}")
    return translations


def build_catalog(fetcher=fetch_json) -> dict:
    if len(COUNTS) != 114 or sum(COUNTS) != 6236:
        raise ValueError("Internal canonical verse-count table is invalid")
    response = fetcher(f"{BASE}/quran/{EDITION}")
    if not isinstance(response, dict) or response.get("code") != 200:
        raise ValueError("Complete translation API did not return HTTP 200 data")
    data = response.get("data")
    surahs = data.get("surahs") if isinstance(data, dict) else None
    if not isinstance(surahs, list) or len(surahs) != 114:
        raise ValueError("Complete translation response must contain all 114 surahs")
    verses: dict[str, str] = {}
    for surah, expected_count in enumerate(COUNTS, 1):
        matching = [item for item in surahs if isinstance(item, dict) and item.get("number") == surah]
        if len(matching) != 1:
            raise ValueError(f"Complete translation response has missing/duplicate surah {surah}")
        payload = {"code": 200, "data": matching[0]}
        verses.update(validate_surah_payload(payload, surah, expected_count))
    if len(verses) != 6236:
        raise ValueError(f"Expected 6,236 translations, received {len(verses)}")
    return {
        "source": "AlQuran Cloud API",
        "source_url": "https://alquran.cloud/",
        "api_documentation": "https://alquran.cloud/api",
        "edition": EDITION,
        "translation_name": "Saheeh International",
        "language": "en",
        "attribution": "Saheeh International, via AlQuran Cloud API (edition en.sahih).",
        "terms_note": "AlQuran Cloud states that translations are contributed by rights-holders or sourced from public-domain editions; republished translations must attribute the translator by name. Commercial reuse rights for this specific edition must be confirmed before monetized distribution.",
        "status": "complete_source_corpus_requires_rights_confirmation_and_verse_level_review",
        "expected_verse_count": 6236,
        "translated_verse_count": len(verses),
        "verses": dict(sorted(verses.items(), key=lambda pair: tuple(map(int, pair[0].split(":"))))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output/saheeh_international_translation.json"))
    args = parser.parse_args()
    catalog = build_catalog()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {catalog['translated_verse_count']} translations from {catalog['translation_name']} ({catalog['edition']})")


if __name__ == "__main__":
    main()

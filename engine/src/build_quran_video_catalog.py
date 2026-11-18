"""Join the complete Arabic, Saheeh translation and official audio catalogs.

The result is a data-preparation candidate only. It cannot be rendered until
Arabic text, translation rights/review, and each exact recording are approved.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CANONICAL_SURAH_VERSE_COUNTS = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]
VERSE_KEY = re.compile(r"^([1-9][0-9]*):([1-9][0-9]*)$")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _validate_verse_keys(keys, expected_count: int) -> set[str]:
    if isinstance(expected_count, bool) or not isinstance(expected_count, int) or expected_count < 1:
        raise ValueError("Expected verse count must be a positive integer.")
    if len(keys) != expected_count:
        raise ValueError(f"All catalogs must contain exactly {expected_count} entries.")
    parsed = set()
    for key in keys:
        if not isinstance(key, str):
            raise ValueError(f"Invalid Quran verse key: {key!r}.")
        match = VERSE_KEY.fullmatch(key)
        if not match:
            raise ValueError(f"Invalid Quran verse key: {key!r}; expected surah:ayah.")
        surah, ayah = map(int, match.groups())
        if not 1 <= surah <= 114:
            raise ValueError(f"Invalid Quran verse key with out-of-range surah number: {key}.")
        if expected_count == 6236 and ayah > CANONICAL_SURAH_VERSE_COUNTS[surah - 1]:
            raise ValueError(f"Quran verse key is outside the canonical surah range: {key}.")
        parsed.add(key)
    if len(parsed) != expected_count:
        raise ValueError("Quran verse keys contain duplicates.")
    if expected_count == 6236:
        canonical = {
            f"{surah}:{ayah}"
            for surah, count in enumerate(CANONICAL_SURAH_VERSE_COUNTS, 1)
            for ayah in range(1, count + 1)
        }
        if parsed != canonical:
            missing = sorted(canonical - parsed)[:5]
            extra = sorted(parsed - canonical)[:5]
            raise ValueError(f"Catalog does not match the canonical 6,236 Quran references; missing={missing}, extra={extra}.")
    return parsed


def build_joined_catalog(arabic: dict, translation: dict, audio: dict, expected_count: int = 6236) -> dict:
    if arabic.get("edition") != "quran-uthmani" or arabic.get("script") != "uthmani":
        raise ValueError("Arabic catalog must be quran-uthmani in Uthmani script.")
    if arabic.get("review_status") != "source_fetched_not_human_reviewed" or arabic.get("rendering_allowed") is not False:
        raise ValueError("Arabic catalog must remain explicitly unreviewed and blocked from rendering.")
    if translation.get("edition") != "en.sahih":
        raise ValueError("Translation catalog must be Saheeh International (en.sahih).")
    if translation.get("status") != "complete_source_corpus_requires_rights_confirmation_and_verse_level_review":
        raise ValueError("Translation rights/review gate is missing.")
    if audio.get("mapped_verse_count") != expected_count:
        raise ValueError("Official audio inventory is not complete.")
    arabic_verses = arabic.get("verses")
    translations = translation.get("verses")
    audio_verses = audio.get("verses")
    if not all(isinstance(value, dict) for value in (arabic_verses, translations, audio_verses)):
        raise ValueError("All three catalogs must contain verse dictionaries.")
    arabic_keys = _validate_verse_keys(arabic_verses, expected_count)
    translation_keys = _validate_verse_keys(translations, expected_count)
    audio_keys = _validate_verse_keys(audio_verses, expected_count)
    if arabic_keys != translation_keys or arabic_keys != audio_keys:
        raise ValueError("Arabic, translation and audio keys do not match exactly.")
    joined = {}
    for key in sorted(arabic_keys, key=lambda value: tuple(map(int, value.split(":")))):
        arabic_text, english_text, audio_member = arabic_verses[key], translations[key], audio_verses[key]
        if not isinstance(arabic_text, str) or not arabic_text.strip():
            raise ValueError(f"Empty Arabic text for {key}.")
        if not isinstance(english_text, str) or not english_text.strip():
            raise ValueError(f"Empty translation for {key}.")
        if not isinstance(audio_member, str) or not audio_member.strip():
            raise ValueError(f"Missing official audio archive member for {key}.")
        joined[key] = {
            "arabic_uthmani": arabic_text,
            "english_saheeh_international": english_text,
            "audio_archive_member": audio_member,
        }
    return {
        "schema_version": 1,
        "status": "complete_join_candidate_requires_human_review_and_recording_approval",
        "rendering_allowed": False,
        "expected_verse_count": expected_count,
        "joined_verse_count": len(joined),
        "join_key": "surah:ayah",
        "sources": {
            "arabic": arabic.get("source_url"),
            "translation": translation.get("source_url"),
            "audio": audio.get("source_url"),
        },
        "review_gates": {
            "arabic_text": "not_human_reviewed",
            "translation": "verse_level_review_and_commercial_reuse_rights_confirmation_required",
            "audio": "exact_recording_must_be_listened_to_and_approved_for_each_selected_passage",
            "background": "must_be_licensed_and_user_approved",
            "publishing": "manual_user_review_only",
        },
        "verses": joined,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arabic", type=Path, required=True)
    parser.add_argument("--translation", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/quran_joined_candidate.json"))
    args = parser.parse_args()
    result = build_joined_catalog(load(args.arabic), load(args.translation), load(args.audio))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Joined {result['joined_verse_count']} Quran verses by exact surah:ayah keys; rendering remains disabled pending review.")


if __name__ == "__main__":
    main()

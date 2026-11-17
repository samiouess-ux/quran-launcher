"""Join the complete Arabic, Saheeh translation and official audio catalogs.

The result is a data-preparation candidate only. It cannot be rendered until
Arabic text, translation rights/review, and each exact recording are approved.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


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
    expected_keys = set()
    # Keys are numeric surah:ayah references, validated by canonical count order
    # in the source builders. The join refuses any discrepancy between catalogs.
    if len(arabic_verses) != expected_count or len(translations) != expected_count or len(audio_verses) != expected_count:
        raise ValueError(f"All catalogs must contain exactly {expected_count} entries.")
    if set(arabic_verses) != set(translations) or set(arabic_verses) != set(audio_verses):
        raise ValueError("Arabic, translation and audio keys do not match exactly.")
    joined = {}
    for key in sorted(arabic_verses, key=lambda value: tuple(map(int, value.split(":")))):
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

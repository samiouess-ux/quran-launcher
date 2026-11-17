"""Build one exact, user-requested Quran passage as a review-only batch."""
from __future__ import annotations
import argparse, json
from pathlib import Path

from parse_telegram_quran_request import SURAH_AYAH_COUNTS


def build_requested_batch(joined: dict, surah: int, start_ayah: int, end_ayah: int) -> dict:
    if joined.get("rendering_allowed") is not False or joined.get("status") != "complete_join_candidate_requires_human_review_and_recording_approval":
        raise ValueError("Only the complete, review-gated joined catalog is accepted.")
    if not 1 <= surah <= 114 or start_ayah < 1 or end_ayah < start_ayah or end_ayah - start_ayah > 9:
        raise ValueError("Request must be one surah and a range of 1–10 consecutive ayahs.")
    if end_ayah > SURAH_AYAH_COUNTS[surah - 1]:
        raise ValueError(f"Requested ayah exceeds the {SURAH_AYAH_COUNTS[surah - 1]} ayahs in this surah.")
    corpus = joined.get("verses")
    refs = [f"{surah}:{ayah}" for ayah in range(start_ayah, end_ayah + 1)]
    verses = []
    for ref in refs:
        row = corpus.get(ref) if isinstance(corpus, dict) else None
        if not isinstance(row, dict):
            raise ValueError(f"Requested ayah is absent from the joined Quran catalog: {ref}")
        values = (row.get("arabic_uthmani"), row.get("english_saheeh_international"), row.get("audio_archive_member"))
        if not all(isinstance(v, str) and v.strip() for v in values):
            raise ValueError(f"Arabic, translation, or audio mapping is incomplete for {ref}.")
        verses.append({"ayah": int(ref.split(":")[1]), "reference": ref,
            "arabic_uthmani": values[0], "english_saheeh_international": values[1],
            "official_audio_archive_member": values[2]})
    candidate_id = f"quran_request_s{surah:03d}_{start_ayah:03d}_{end_ayah:03d}"
    return {"schema_version": 1, "batch_status": "review_candidates_only", "seed": candidate_id,
        "candidate_count": 1, "distinct_surah_count": 1, "verses_per_passage": len(verses),
        "source_catalog_status": joined["status"], "rendering_allowed": False,
        "auto_publish": False, "telegram_delivery": False,
        "note": "Explicit user-requested passage. Review and rights approval remain mandatory.",
        "passages": [{"candidate_id": candidate_id, "surah_number": surah,
            "verse_numbers": list(range(start_ayah, end_ayah + 1)), "verses": verses,
            "status": "candidate_requires_human_review",
            "approval": {"arabic_text_reviewed": False, "translation_rights_confirmed": False,
                "exact_recitation_listened_to": False, "recording_reuse_approved": False,
                "background_licensed_and_user_approved": False, "ready_to_render": False,
                "ready_to_publish": False}}]}


def save_batch(batch: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--surah", type=int, required=True)
    parser.add_argument("--start-ayah", type=int, required=True)
    parser.add_argument("--end-ayah", type=int, required=True)
    parser.add_argument("--output", type=Path, default=Path("output/quran_requested_batch.json"))
    args = parser.parse_args()
    joined = json.loads(args.catalog.read_text(encoding="utf-8"))
    batch = build_requested_batch(joined, args.surah, args.start_ayah, args.end_ayah)
    save_batch(batch, args.output)
    print(f"Prepared {batch['passages'][0]['candidate_id']} as a review-only request.")


if __name__ == "__main__":
    main()

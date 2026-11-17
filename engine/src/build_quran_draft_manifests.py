"""Generate draft Quran manifests from the multi-surah batch and audio report.

Drafts are deliberately NOT renderable: exact recitation, reuse rights,
Arabic/translation review, and an approved background remain mandatory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_draft_manifests(batch: dict[str, Any], report: dict[str, Any], output_dir: Path) -> list[dict]:
    if batch.get("batch_status") != "review_candidates_only":
        raise ValueError("Only review candidate batches are accepted.")
    if report.get("rendering_allowed") is not False or report.get("auto_publish") is not False:
        raise ValueError("Audio report must remain review-only.")
    passages = {item["candidate_id"]: item for item in batch.get("passages", [])}
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for audio_item in report.get("items", []):
        if not audio_item.get("status", "").startswith("audio_prepared"):
            continue
        source_candidate_id = audio_item.get("source_candidate_id", audio_item["candidate_id"])
        candidate = passages.get(source_candidate_id)
        if not candidate:
            raise ValueError(f"Audio candidate missing from batch: {audio_item['candidate_id']}")
        if int(candidate["surah_number"]) != int(audio_item["surah_number"]):
            raise ValueError("Surah mismatch between batch and audio report.")
        candidate_by_number = {int(v["ayah"]): v for v in candidate["verses"]}
        requested = audio_item.get("requested_verses")
        expected = audio_item.get("selected_verses")
        candidate_numbers = [int(v["ayah"]) for v in candidate["verses"]]
        if not isinstance(requested, list) or [int(n) for n in requested] != candidate_numbers:
            raise ValueError("Prepared audio request must match every source candidate ayah in order.")
        if not isinstance(expected, list) or not expected:
            raise ValueError("Prepared audio must select a non-empty contiguous ayah range.")
        start = requested.index(int(expected[0])) if int(expected[0]) in requested else -1
        if start < 0 or [int(n) for n in expected] != [int(n) for n in requested[start:start + len(expected)]]:
            raise ValueError("Prepared audio must select a contiguous slice of the requested ayahs.")
        if expected != list(range(int(expected[0]), int(expected[0]) + len(expected))):
            raise ValueError("Prepared audio ayahs must be a contiguous ordered passage.")
        if not audio_item.get("audio_file"):
            raise ValueError("Prepared audio file path is missing.")
        selected_source = [candidate_by_number[int(n)] for n in expected]
        verses = [{
            "number": int(v["ayah"]),
            "arabic": v["arabic_uthmani"].lstrip("\ufeff"),
            "english": v["english_saheeh_international"],
        } for v in selected_source]
        surah = int(candidate["surah_number"])
        from render_quran_review_previews import SURAH_NAMES
        if not 1 <= surah <= len(SURAH_NAMES):
            raise ValueError(f"Invalid Quran surah number: {surah}")
        surah_name_ar = SURAH_NAMES[surah - 1]
        source_durations = audio_item["verse_durations_seconds"]
        processed_durations = audio_item.get("processed_verse_durations_seconds") or source_durations
        manifest = {
            "id": audio_item["candidate_id"],
            "source_candidate_id": source_candidate_id,
            "part_index": int(audio_item.get("part_index", 1)),
            "part_count": int(audio_item.get("part_count", 1)),
            "content_type": "quran",
            "status": "draft_candidate_requires_human_review",
            "rotation_approved": False,
            "source": {
                "surah_number": surah,
                "surah_name_ar": surah_name_ar,
                "verses": expected,
                "references": [v["reference"] for v in selected_source],
                "arabic_source": "Quran Uthmani joined candidate catalog; not yet human-reviewed",
                "translation_name": "Saheeh International",
                "translation_rights_confirmed": False,
            },
            "verses": verses,
            "audio": {
                "required": True,
                "kind": "quran_recitation",
                "production_audio_file": audio_item["audio_file"],
                "source_verse_durations_seconds": {str(k): v for k, v in source_durations.items()},
                "processed_verse_durations_seconds": {str(k): v for k, v in processed_durations.items()},
                "edge_silence_removed_seconds": audio_item.get("edge_silence_removed_seconds", {}),
                "inter_verse_silence_seconds": float(audio_item.get("inter_verse_silence_seconds", 0.24)),
                "approved": False,
                "preview_only": False,
                "exact_recording_user_reviewed": False,
                "rights_verified": False,
                "music_allowed": False,
                "notes": "Official whole-ayah MP3 files remain in order. Only detected leading/trailing silence is reduced with a 0.12-second safety margin; internal recitation is untouched and MP3 frames are stream-copied. Listen to this exact file and verify reuse rights before rendering.",
            },
            "visual": {
                "format": "9:16",
                "width": 1080,
                "height": 1920,
                "fps": 30,
                "template": "ornate_gold_classic",
                "template_approved": True,
                "background_style": "awaiting approved background",
                "background_candidate": {},
            },
            "publishing": {
                "approval_required": True,
                "auto_publish": False,
                "telegram_delivery": False,
                "manual_review_required": True,
            },
            "caption": {
                "text": f"سورة {surah_name_ar} | الآيات {expected[0]}-{expected[-1]}",
                "references": [v["reference"] for v in selected_source],
            },
            "preflight": {
                "audio_duration_seconds": audio_item["duration_seconds"],
                "audio_approved": False,
                "rendering_allowed": False,
                "telegram_delivery": False,
                "auto_publish": False,
                "blockers": [
                    "human verification of exact Arabic text",
                    "translation reuse rights confirmation",
                    "listen to and approve the exact recitation",
                    "document recording reuse permission",
                    "select and explicitly approve a licensed background",
                ],
            },
        }
        path = output_dir / f"{audio_item['candidate_id']}.json"
        if path.exists():
            raise ValueError(f"Refusing to overwrite draft manifest: {path}")
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        created.append({"candidate_id": audio_item["candidate_id"], "source_candidate_id": source_candidate_id, "part_index": int(audio_item.get("part_index", 1)), "surah_number": surah, "verses": expected, "manifest": str(path), "rendering_allowed": False})
    if not created:
        raise ValueError("At least one prepared whole-ayah audio part is required for this scheduled slot.")
    if len({item["candidate_id"] for item in created}) != len(created):
        raise ValueError("Draft manifests must have unique part identifiers.")
    return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--audio-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("output/quran_draft_manifests"))
    parser.add_argument("--report", type=Path, default=Path("output/quran_draft_manifest_report.json"))
    args = parser.parse_args()
    result = build_draft_manifests(
        json.loads(args.batch.read_text(encoding="utf-8")),
        json.loads(args.audio_report.read_text(encoding="utf-8")),
        args.output_dir,
    )
    summary = {
        "status": "draft_manifests_generated_for_review",
        "manifest_count": len(result),
        "distinct_surah_count": len({x["surah_number"] for x in result}),
        "preview_part_count": len(result),
        "items": result,
        "rendering_allowed": False,
        "telegram_delivery": False,
        "auto_publish": False,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

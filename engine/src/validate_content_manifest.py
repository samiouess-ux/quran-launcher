"""Shared fail-closed validation for Quran and dua/dhikr content manifests.

This module validates metadata and safety gates only. It does not authenticate
religious wording or grant audio/background rights; those require trusted
sources and explicit human review recorded in the manifest.
"""
from __future__ import annotations

from typing import Any


CONTENT_TYPES = {"quran", "dua", "dhikr"}
AUDIO_KINDS = {"quran_recitation", "spoken_dua", "ambient_nature", "silent"}


def validate_content_manifest(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise SystemExit("Manifest must be a JSON object.")

    content_type = data.get("content_type")
    if content_type not in CONTENT_TYPES:
        raise SystemExit("content_type must be explicitly set to quran, dua, or dhikr.")

    source = data.get("source")
    visual = data.get("visual")
    audio = data.get("audio")
    publishing = data.get("publishing")
    if not all(isinstance(x, dict) for x in (source, visual, audio, publishing)):
        raise SystemExit("source, visual, audio and publishing must be objects.")

    if publishing.get("auto_publish") is not False:
        raise SystemExit("Auto-publishing must remain disabled.")
    if publishing.get("approval_required") is not True:
        raise SystemExit("Every video must require explicit user review.")

    template = visual.get("template", "ornate_gold_classic")
    supported_templates = {"ornate_gold_classic", "nature_clean", "minimal_mushaf", "cinematic_landscape"}
    if template not in supported_templates:
        raise SystemExit(f"Unsupported visual template: {template}.")
    if template != "ornate_gold_classic" and visual.get("template_approved") is not True:
        raise SystemExit("A new visual template must be explicitly approved before production rendering.")
    background = visual.get("background_candidate", {})
    if not isinstance(background, dict):
        raise SystemExit("visual.background_candidate must be an object.")
    if not background.get("direct_video_url") or not background.get("source_url"):
        raise SystemExit("Background source and direct video URLs are required.")
    if background.get("approved") is not True or background.get("user_approved") is not True:
        raise SystemExit("Background must be approved and user-reviewed.")
    if background.get("download_verified") is not True:
        raise SystemExit("Background file must be downloaded and technically verified.")

    kind = audio.get("kind")
    if kind not in AUDIO_KINDS:
        raise SystemExit("audio.kind must explicitly identify the audio type.")
    if audio.get("music_allowed", False):
        raise SystemExit("Music is not allowed.")

    if content_type == "quran":
        if kind != "quran_recitation":
            raise SystemExit("Quran content requires authentic Quran recitation.")
        preview_only = audio.get("preview_only") is True
        approved = audio.get("approved", audio.get("approved_for_first_test_video", False)) is True
        if not approved and not preview_only:
            raise SystemExit("Quran recitation is not approved; only an explicit preview_only candidate may be rendered for review.")
        if preview_only and approved:
            raise SystemExit("A preview_only Quran recording cannot also be marked production-approved.")
        reviewed = audio.get("exact_recording_user_reviewed", False) or any(
            item.get("exact_recording_user_reviewed", False)
            for item in audio.get("license_research_candidates", [])
            if isinstance(item, dict)
        )
        if not reviewed and not preview_only:
            raise SystemExit("Exact Quran recording has not been user-reviewed.")
        rights_verified = audio.get("rights_verified") or any(
            item.get("status", "").startswith("approved_")
            for item in audio.get("license_research_candidates", [])
            if isinstance(item, dict)
        )
        if not rights_verified:
            raise SystemExit("Reuse permission for the exact Quran recording is not documented.")
        if not source.get("surah_number") or not source.get("verses"):
            raise SystemExit("Quran source must identify a surah and requested verses.")
        verses = data.get("verses")
        if not isinstance(verses, list) or not verses:
            raise SystemExit("Quran manifest must contain verified verses.")
        numbers = [v.get("number") for v in verses if isinstance(v, dict)]
        if len(numbers) != len(verses) or numbers != source["verses"]:
            raise SystemExit("Quran verse entries must exactly match source.verses in order.")
        for verse in verses:
            if not isinstance(verse.get("arabic"), str) or not verse["arabic"].strip():
                raise SystemExit("Every Quran verse needs exact Arabic text.")
            if not isinstance(verse.get("english"), str) or not verse["english"].strip():
                raise SystemExit("Every Quran verse needs its verified translation.")
    else:
        if not data.get("items") or not isinstance(data["items"], list):
            raise SystemExit("Dua/dhikr manifest must contain sourced items.")
        for item in data["items"]:
            if not isinstance(item, dict) or not isinstance(item.get("arabic"), str) or not item["arabic"].strip():
                raise SystemExit("Every dua/dhikr item needs its exact Arabic wording.")
            if not item.get("source_name") or not str(item.get("source_url", "")).startswith("https://"):
                raise SystemExit("Every dua/dhikr item needs a named HTTPS religious source.")
        if kind == "quran_recitation":
            raise SystemExit("Dua/dhikr audio must not be mislabeled as Quran recitation.")
        if kind in {"spoken_dua", "ambient_nature"}:
            if not audio.get("approved") or not audio.get("rights_verified"):
                raise SystemExit("Dua/dhikr audio needs approval and documented reuse permission.")
            if kind == "spoken_dua" and not audio.get("exact_recording_user_reviewed"):
                raise SystemExit("Exact spoken-dua recording must be user-reviewed.")
            if kind == "ambient_nature" and not audio.get("user_approved"):
                raise SystemExit("Ambient audio must be explicitly user-approved.")
        if kind == "silent" and audio.get("file"):
            raise SystemExit("Silent content must not declare an audio file.")

"""Deterministic, restrained multilingual hashtag rotation for Quran videos."""
from __future__ import annotations

import hashlib
from typing import Any

ROTATIONS = (
    {"ar": "#القرآن_الكريم", "en": "#Quran", "fr": "#Coran", "tr": "#Kuran", "id": "#AlQuran"},
    {"ar": "#آيات_قرآنية", "en": "#QuranVerses", "fr": "#RappelIslamique", "tr": "#KuranTilaveti", "id": "#Tilawah"},
    {"ar": "#تلاوة_خاشعة", "en": "#QuranRecitation", "fr": "#Foi", "tr": "#Islam", "id": "#Islam"},
    {"ar": "#تدبر_القرآن", "en": "#IslamicReminder", "fr": "#Spiritualite", "tr": "#Musluman", "id": "#Muslim"},
    {"ar": "#ذكر_الله", "en": "#MuslimReminder", "fr": "#LectureDuCoran", "tr": "#KuraniKerim", "id": "#PengingatIslam"},
)

TOPIC_TAGS = {
    "ease_after_hardship": {"ar": "#مع_العسر_يسرا", "en": "#EaseAfterHardship"},
    "patience": {"ar": "#الصبر", "en": "#PatienceInIslam"},
    "gratitude": {"ar": "#الحمد_لله", "en": "#GratitudeToAllah"},
    "prayer": {"ar": "#الصلاة", "en": "#Salah"},
    "mercy": {"ar": "#رحمة_الله", "en": "#MercyOfAllah"},
}

def _valid_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [tag for tag in value if isinstance(tag, str) and tag.startswith("#") and not any(ch.isspace() for ch in tag)]

def build_hashtags(video_id: str, caption: dict[str, Any]) -> dict[str, list[str]]:
    """Build a reproducible multilingual set; unknown topics add no tags."""
    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("A stable, non-empty video id is required for hashtag rotation.")
    if not isinstance(caption, dict):
        raise ValueError("Caption metadata must be an object.")
    digest = hashlib.sha256(video_id.encode("utf-8")).digest()
    rotation_index = int.from_bytes(digest[:8], "big") % len(ROTATIONS)
    rotation = ROTATIONS[rotation_index]
    topics = caption.get("hashtag_topics", [])
    if isinstance(topics, str):
        topics = [topics]
    if not isinstance(topics, list):
        topics = []
    topic_tags = {"ar": [], "en": []}
    for topic in topics:
        if isinstance(topic, str):
            selected = TOPIC_TAGS.get(topic)
            if selected:
                for language, tag in selected.items():
                    topic_tags[language].append(tag)
    result: dict[str, list[str]] = {}
    for language in ("ar", "en", "fr", "tr", "id"):
        supplied = _valid_tags(caption.get(f"hashtags_{language}", []))
        chosen_supplied = [supplied[rotation_index % len(supplied)]] if supplied else []
        candidates = chosen_supplied + topic_tags.get(language, []) + [rotation[language]]
        unique: list[str] = []
        for tag in candidates:
            if tag not in unique:
                unique.append(tag)
        result[language] = unique[:2]
    return result

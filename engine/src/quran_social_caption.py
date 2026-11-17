"""Content-aware Arabic/English captions and exactly-five hashtag sets."""
from __future__ import annotations

import hashlib
from typing import Any

THEMES = (
    ("patience", ("patience", "patient", "persevere", "hardship", "ease", "fear", "grief"),
     "الصبر والثبات عند الشدائد، وأن مع العسر يسراً",
     "patience, perseverance, and hope through hardship",
     "#الصبر_والفرج", "#PatienceAndHope"),
    ("mercy", ("mercy", "forgiving", "forgive", "compassion", "merciful", "forgiven"),
     "رحمة الله ومغفرته، وفتح باب الرجوع إليه",
     "Allah’s mercy, forgiveness, and the door of repentance",
     "#رحمة_ومغفرة", "#MercyAndForgiveness"),
    ("prayer", ("prayer", "pray", "worship", "prostrate", "righteous deeds"),
     "الإخلاص في العبادة والمحافظة على الصلاة والعمل الصالح",
     "sincere worship, prayer, and righteous deeds",
     "#الصلاة_والعبادة", "#PrayerAndWorship"),
    ("gratitude", ("thankful", "thanks", "gratitude", "blessing", "favor"),
     "شكر نعم الله والاعتراف بفضله",
     "gratitude for Allah’s blessings",
     "#الشكر_والنعم", "#GratitudeToAllah"),
    ("guidance", ("guide", "guidance", "path", "believe", "faith", "light"),
     "الهداية والإيمان والثبات على الطريق المستقيم",
     "faith, guidance, and steadfastness on the straight path",
     "#الهداية_والإيمان", "#FaithAndGuidance"),
    ("afterlife", ("resurrection", "judgment", "paradise", "hell", "hereafter", "day of"),
     "الآخرة والجزاء وتذكّر الوقوف بين يدي الله",
     "the Hereafter, accountability, and the final return to Allah",
     "#الآخرة_والحساب", "#HereafterReminder"),
    ("tawheed", ("one god", "one", "eternal refuge", "begets", "equivalent", "creator"),
     "توحيد الله وتعظيمه وإفراده بالعبادة",
     "the oneness of Allah and devotion to Him alone",
     "#توحيد_الله", "#Tawheed"),
)

AR_CORE = (
    ("#القرآن_الكريم", "#تلاوة_قرآنية"),
    ("#آيات_قرآنية", "#تدبر_القرآن"),
    ("#ذكر_الله", "#نور_القرآن"),
    ("#القرآن", "#تذكير_إيماني"),
    ("#كلام_الله", "#تلاوة_خاشعة"),
)
EN_CORE = ("#Quran", "#QuranVerses", "#QuranRecitation", "#IslamicReminder", "#ReflectOnQuran")


def detect_theme(verses: list[dict[str, Any]]) -> tuple[str, str, str, str, str]:
    text = " ".join(str(v.get("english", "")) for v in verses).lower()
    scored = []
    for theme in THEMES:
        score = sum(text.count(word) for word in theme[1])
        if score:
            scored.append((score, theme))
    if not scored:
        return ("general", "وتدعونا الآيات إلى الإيمان بالله والعمل بالخير والتدبّر في هديه",
                "these verses invite faith, reflection, and righteous action",
                "#تدبر_وعمل", "#QuranReflection")
    selected = max(scored, key=lambda item: (item[0], -THEMES.index(item[1])))[1]
    return selected[0], selected[2], selected[3], selected[4], selected[5]


def build_social_caption(manifest: dict[str, Any], video_id: str) -> dict[str, Any]:
    if not isinstance(manifest, dict) or not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("A manifest and stable non-empty video id are required.")
    source = manifest.get("source", {})
    verses = manifest.get("verses", [])
    if not isinstance(verses, list) or not verses:
        raise ValueError("Caption requires at least one selected verse.")
    name = str(source.get("surah_name_ar", "")).strip()
    english_name = str(source.get("surah_name_en", "")).strip()
    numbers = source.get("verses", [])
    if not name or not isinstance(numbers, list) or not numbers:
        raise ValueError("Caption requires the surah name and selected ayah numbers.")
    first, last = int(numbers[0]), int(numbers[-1])
    theme, description_ar, description_en, topic_ar, topic_en = detect_theme(verses)
    digest = hashlib.sha256(video_id.encode("utf-8")).digest()
    rotation = int.from_bytes(digest[:4], "big")
    ar_pair = AR_CORE[rotation % len(AR_CORE)]
    en_tag = EN_CORE[(rotation // len(AR_CORE)) % len(EN_CORE)]
    tags = [ar_pair[0], ar_pair[1], en_tag, topic_ar, topic_en]
    # Stable de-duplication and exact five-tag contract.
    unique = list(dict.fromkeys(tags))
    fallback = [tag for pair in AR_CORE for tag in pair] + list(EN_CORE)
    for tag in fallback:
        if len(unique) == 5:
            break
        if tag not in unique:
            unique.append(tag)
    return {
        "arabic_caption": f"سورة {name} | الآيات {first}-{last}\n{description_ar}. استمع وتدبّر.",
        "english_caption": f"Surah {english_name or name} | Verses {first}-{last}. {description_en.capitalize()}. Listen and reflect.",
        "hashtags_ar": [tag for tag in unique if tag.startswith("#") and any("\\u0600" <= ch <= "\\u06ff" for ch in tag)],
        "hashtags_en": [tag for tag in unique if tag.startswith("#") and not any("\\u0600" <= ch <= "\\u06ff" for ch in tag)],
        "theme": theme,
    }

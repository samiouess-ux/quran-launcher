"""Parse a user's Telegram Quran video request without triggering rendering or delivery."""
from __future__ import annotations

import re
import unicodedata

SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف",
    "الأنفال", "التوبة", "يونس", "هود", "يوسف", "الرعد", "إبراهيم", "الحجر",
    "النحل", "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون",
    "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر",
    "غافر", "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد",
    "الفتح", "الحجرات", "ق", "الذاريات", "الطور", "النجم", "القمر", "الرحمن",
    "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة", "الصف", "الجمعة",
    "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة",
    "المعارج", "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان",
    "المرسلات", "النبأ", "النازعات", "عبس", "التكوير", "الانفطار", "المطففين",
    "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة",
    "الزلزلة", "العاديات", "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل",
    "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص",
    "الفلق", "الناس",
]

SURAH_AYAH_COUNTS = [7,286,200,176,120,165,206,75,129,109,123,111,43,52,99,128,111,110,98,135,112,78,118,64,77,227,93,88,69,60,34,30,73,54,45,83,182,88,75,85,54,53,89,59,37,35,38,29,18,45,60,49,62,55,78,96,29,22,24,13,14,11,11,18,12,12,30,52,52,44,28,28,20,56,40,31,50,40,46,42,29,19,36,25,22,17,19,26,30,20,15,21,11,8,8,19,5,8,8,11,11,8,3,9,5,4,7,3,6,3,5,4,5,6]

_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _clean(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).translate(_TRANSLATION)
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    value = re.sub(r"[ًٌٍَُِّْـ]", "", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def parse_quran_request(message: str) -> dict:
    """Accept e.g. 'فيديو سورة الرحمن' or 'فيديو سورة البقرة الآيات 1-5'."""
    if not isinstance(message, str) or not message.strip():
        raise ValueError("ابعث اسم السورة، مثال: فيديو سورة الرحمن")
    cleaned = _clean(message)
    cleaned = re.sub(r"^(?:(?:اريد|نحب|اعمل|حضر)\s+)?(?:فيديو\s+)?سورة\s+", "", cleaned)
    match = re.fullmatch(
        r"(?P<name>.+?)(?:\s+(?:الايات|الاية|الآية|اية|آية|من)\s*(?P<start>\d+)(?:\s*(?:-|الى|إلى|ل)\s*(?P<end>\d+))?)?",
        cleaned,
    )
    if not match:
        raise ValueError("الصيغة موش واضحة. مثال: فيديو سورة البقرة الآيات 1-5")
    requested_name = match.group("name").strip()
    names = {_clean(name): i + 1 for i, name in enumerate(SURAH_NAMES)}
    surah = names.get(requested_name)
    if surah is None:
        raise ValueError("ما تعرفتش على اسم السورة. ابعث الاسم العربي الصحيح.")
    has_ayah_request = match.group("start") is not None
    start = int(match.group("start") or 1)
    end = int(match.group("end")) if match.group("end") is not None else (start if has_ayah_request else None)
    if start < 1 or (end is not None and (end < start or end - start > 9)):
        raise ValueError("الطلب لازم يكون من آية إلى 10 آيات متتالية.")
    if start > SURAH_AYAH_COUNTS[surah - 1] or (end is not None and end > SURAH_AYAH_COUNTS[surah - 1]):
        raise ValueError("رقم الآية يتجاوز آخر آية في السورة المطلوبة.")
    return {
        "surah_number": surah,
        "surah_name": SURAH_NAMES[surah - 1],
        "start_ayah": start,
        "end_ayah": end,
        "request_type": "single_surah_passage" if has_ayah_request else "full_surah",
        "status": "parsed_only_not_rendered_not_sent",
        "rendering_allowed": False,
        "telegram_delivery": False,
        "auto_publish": False,
    }

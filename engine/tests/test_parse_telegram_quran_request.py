import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from parse_telegram_quran_request import parse_quran_request


class TelegramQuranRequestParserTests(unittest.TestCase):
    def test_full_surah_request_defaults_to_first_ayah_only(self):
        result = parse_quran_request("فيديو سورة الرحمن")
        self.assertEqual(result["surah_number"], 55)
        self.assertEqual(result["surah_name"], "الرحمن")
        self.assertEqual(result["request_type"], "full_surah")
        self.assertEqual((result["start_ayah"], result["end_ayah"]), (1, None))

    def test_arabic_name_and_arabic_indic_ayah_range(self):
        result = parse_quran_request("نحب فيديو سورة البقرة الآيات ١-٥")
        self.assertEqual(result["surah_number"], 2)
        self.assertEqual((result["start_ayah"], result["end_ayah"]), (1, 5))

    def test_latin_digits_and_single_ayah(self):
        result = parse_quran_request("سورة يس الآيات 12-12")
        self.assertEqual(result["surah_number"], 36)
        self.assertEqual((result["start_ayah"], result["end_ayah"]), (12, 12))

    def test_single_ayah_request_is_supported(self):
        result = parse_quran_request("نحب فيديو سورة الكهف الآية 5")
        self.assertEqual(result["surah_number"], 18)
        self.assertEqual((result["start_ayah"], result["end_ayah"]), (5, 5))
        self.assertEqual(result["request_type"], "single_surah_passage")

    def test_unknown_surah_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "اسم السورة"):
            parse_quran_request("فيديو سورة غير موجودة")

    def test_more_than_ten_ayahs_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "10 آيات"):
            parse_quran_request("سورة البقرة الآيات 1-11")

    def test_ayah_beyond_surah_length_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "يتجاوز آخر آية"):
            parse_quran_request("سورة الفاتحة الآيات 1-8")

    def test_full_surah_request_starts_with_valid_first_ayah(self):
        result = parse_quran_request("فيديو سورة الكوثر")
        self.assertEqual(result["surah_number"], 108)
        self.assertEqual(result["start_ayah"], 1)

    def test_parser_never_approves_rendering_or_delivery(self):
        result = parse_quran_request("سورة الفاتحة")
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from build_quran_review_batch import build_review_batch, most_recent_delivered_surah

class BatchTests(unittest.TestCase):
    def test_never_reuses_previously_delivered_ayahs(self):
        verses = {}
        for surah in range(1, 7):
            for ayah in range(1, 7):
                key = f"{surah}:{ayah}"
                verses[key] = {"arabic_uthmani": f"AR {key}", "english_saheeh_international": f"EN {key}", "audio_archive_member": f"{key}.mp3"}
        source = {"status": "complete_join_candidate_requires_human_review_and_recording_approval", "rendering_allowed": False, "expected_verse_count": len(verses), "verses": verses}
        used = [f"{surah}:{ayah}" for surah in range(1, 7) for ayah in (1, 2)]
        result = build_review_batch(source, count=4, verses_per_passage=2, seed="history-test", excluded_surahs=[2], used_ayah_references=used)
        selected = [verse["reference"] for passage in result["passages"] for verse in passage["verses"]]
        self.assertTrue(set(selected).isdisjoint(used))

    def test_friday_mode_keeps_al_kahf_and_starts_at_first_unused_ayah(self):
        verses = {}
        for ayah in range(1, 7):
            key = f"18:{ayah}"
            verses[key] = {"arabic_uthmani": f"AR {key}", "english_saheeh_international": f"EN {key}", "audio_archive_member": f"{key}.mp3"}
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="friday-1", used_ayah_references=["18:1", "18:2"],
            only_surahs=[18], sequential_unused=True,
        )
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["passages"][0]["surah_number"], 18)
        self.assertEqual(result["passages"][0]["verse_numbers"], [3, 4, 5, 6])
        self.assertEqual(result["passage_selection"], "first_unused_contiguous_suffix_then_40_second_duration_limit")
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])
    def test_default_starts_at_first_unused_ayah(self):
        verses = {}
        for ayah in range(1, 7):
            key = f"18:{ayah}"
            verses[key] = {"arabic_uthmani": f"AR {key}", "english_saheeh_international": f"EN {key}", "audio_archive_member": f"{key}.mp3"}
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="random-seed-must-not-skip-opening",
            used_ayah_references=["18:1", "18:2"], only_surahs=[18],
        )
        self.assertEqual(result["passages"][0]["verse_numbers"], [3, 4, 5, 6])
        self.assertEqual(
            result["passage_selection"],
            "first_unused_contiguous_suffix_then_40_second_duration_limit",
        )

    def test_prioritizes_continuation_of_partially_delivered_surah(self):
        verses = {}
        for surah in range(1, 7):
            for ayah in range(1, 7):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3",
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=2, seed="continuation-priority",
            used_ayah_references=["5:1", "5:2", "5:3", "5:4"],
        )
        self.assertEqual(result["passages"][0]["surah_number"], 5)
        self.assertEqual(result["passages"][0]["verse_numbers"], [5, 6])
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])

    def test_prioritizes_partial_surah_continuation_in_production_mode(self):
        verses = {}
        for surah in range(1, 7):
            for ayah in range(1, 7):
                key = f"{surah}:{ayah}"
                verses[key] = {"arabic_uthmani": f"AR {key}", "english_saheeh_international": f"EN {key}", "audio_archive_member": f"{key}.mp3"}
        source = {"status": "complete_join_candidate_requires_human_review_and_recording_approval", "rendering_allowed": False, "expected_verse_count": len(verses), "verses": verses}
        result = build_review_batch(source, count=2, seed="production-continuation", used_ayah_references=["5:1", "5:2", "5:3", "5:4"], used_surahs={5})
        self.assertEqual(result["passages"][0]["surah_number"], 5)
        self.assertEqual(result["passages"][0]["verse_numbers"], [5, 6])
        self.assertNotIn(5, [item["surah_number"] for item in result["passages"][1:]])
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])

    def test_fully_delivered_surah_is_not_reselected_as_continuation(self):
        verses = {}
        for surah in range(1, 7):
            for ayah in range(1, 7):
                key = f"{surah}:{ayah}"
                verses[key] = {"arabic_uthmani": f"AR {key}", "english_saheeh_international": f"EN {key}", "audio_archive_member": f"{key}.mp3"}
        source = {"status": "complete_join_candidate_requires_human_review_and_recording_approval", "rendering_allowed": False, "expected_verse_count": len(verses), "verses": verses}
        result = build_review_batch(source, count=2, seed="completed-surah", used_ayah_references=[f"5:{n}" for n in range(1, 7)], used_surahs={5})
        self.assertNotIn(5, [item["surah_number"] for item in result["passages"]])
    def test_continuation_skips_gaps_and_later_delivered_ayahs(self):
        verses = {}
        for ayah in range(1, 7):
            key = f"18:{ayah}"
            verses[key] = {
                "arabic_uthmani": f"AR {key}",
                "english_saheeh_international": f"EN {key}",
                "audio_archive_member": f"{key}.mp3",
            }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="gap-continuation",
            used_ayah_references=["18:1", "18:2", "18:4"],
            only_surahs=[18], sequential_unused=True,
        )
        self.assertEqual(result["passages"][0]["verse_numbers"], [5, 6])
        selected = {
            verse["reference"]
            for passage in result["passages"]
            for verse in passage["verses"]
        }
        self.assertTrue(selected.isdisjoint({"18:1", "18:2", "18:4"}))

    def test_excludes_most_recently_delivered_surah(self):
        history = {"deliveries": [
            {"candidate_id": "old", "surah_number": 18},
            {"candidate_id": "latest", "surah_number": 86},
        ]}
        self.assertEqual(most_recent_delivered_surah(history), 86)
        self.assertIsNone(most_recent_delivered_surah({"deliveries": []}))

    def test_rejects_invalid_latest_surah_in_history(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 114"):
            most_recent_delivered_surah({"deliveries": [{"surah_number": 115}]})

    def test_rejects_malformed_used_ayah_reference(self):
        verses = {"1:1": {"arabic_uthmani": "AR", "english_saheeh_international": "EN", "audio_archive_member": "1.mp3"}}
        source = {"status": "complete_join_candidate_requires_human_review_and_recording_approval", "rendering_allowed": False, "expected_verse_count": 1, "verses": verses}
        with self.assertRaisesRegex(ValueError, "invalid Quran verse reference"):
            build_review_batch(source, count=1, used_ayah_references=["1:0"])

    def test_rejects_history_reference_missing_from_joined_catalog(self):
        verses = {"1:1": {"arabic_uthmani": "AR", "english_saheeh_international": "EN", "audio_archive_member": "1.mp3"}}
        source = {"status": "complete_join_candidate_requires_human_review_and_recording_approval", "rendering_allowed": False, "expected_verse_count": 1, "verses": verses}
        with self.assertRaisesRegex(ValueError, "missing from the joined catalog"):
            build_review_batch(source, count=1, used_ayah_references=["1:2"])

    def test_rejects_malformed_joined_catalog_reference(self):
        for invalid_reference in ("1:0", "1:x", "115:1", 1):
            with self.subTest(reference=invalid_reference):
                verses = {invalid_reference: {"arabic_uthmani": "AR", "english_saheeh_international": "EN", "audio_archive_member": "1.mp3"}}
                source = {"status": "complete_join_candidate_requires_human_review_and_recording_approval", "rendering_allowed": False, "expected_verse_count": 1, "verses": verses}
                with self.assertRaisesRegex(ValueError, "invalid Quran verse reference"):
                    build_review_batch(source, count=1)

    def test_builds_distinct_surahs(self):
        verses = {}
        for surah in range(1, 7):
            for ayah in range(1, 5):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3"
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses
        }
        result = build_review_batch(source, count=4, verses_per_passage=2, seed="test", excluded_surahs=[2])
        self.assertEqual(result["distinct_surah_count"], 4)
        self.assertNotIn(2, [item["surah_number"] for item in result["passages"]])
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["auto_publish"])
        self.assertFalse(result["telegram_delivery"])
        for passage in result["passages"]:
            nums = passage["verse_numbers"]
            self.assertEqual(nums, list(range(nums[0], nums[0] + 2)))


    def test_rotation_continues_partially_delivered_surahs_before_fresh_surahs(self):
        verses = {}
        for surah in range(1, 7):
            for ayah in range(1, 5):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3",
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=2, seed="rotation-test",
            used_ayah_references=["1:1", "1:2", "2:1", "2:2"],
            used_surahs=[1, 2],
        )
        selected = {item["surah_number"]: item["verse_numbers"] for item in result["passages"]}
        self.assertEqual(selected, {1: [3, 4], 2: [3, 4]})
        self.assertEqual(len(selected), 2)
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])

    def test_rotation_continues_partially_delivered_surah_before_fresh_surahs(self):
        verses = {}
        for surah in range(1, 5):
            for ayah in range(1, 5):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3",
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="continue-partial",
            used_ayah_references=["3:1", "3:2"],
            used_surahs=[3],
        )
        self.assertEqual(result["passages"][0]["surah_number"], 3)
        self.assertEqual(result["passages"][0]["verse_numbers"], [3, 4])


    def test_production_continuation_skips_later_used_ayah_after_a_gap(self):
        verses = {}
        for surah in range(1, 5):
            for ayah in range(1, 7):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3",
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="production-gap-continuation",
            used_ayah_references=["3:1", "3:2", "3:4"],
            used_surahs={3},
        )
        self.assertEqual(result["passages"][0]["surah_number"], 3)
        self.assertEqual(result["passages"][0]["verse_numbers"], [5, 6])
        selected = {
            verse["reference"]
            for passage in result["passages"]
            for verse in passage["verses"]
        }
        self.assertTrue(selected.isdisjoint({"3:1", "3:2", "3:4"}))
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])

    def test_selects_last_partial_surah_when_no_fresh_surahs_remain(self):
        verses = {}
        for surah in (1, 2):
            for ayah in range(1, 4):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3",
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="only-partial-left",
            used_ayah_references=["1:1", "1:2", "2:1", "2:2", "2:3"],
            used_surahs={1, 2},
        )
        self.assertEqual(result["passages"][0]["surah_number"], 1)
        self.assertEqual(result["passages"][0]["verse_numbers"], [3])
        self.assertFalse(result["rendering_allowed"])
        self.assertFalse(result["telegram_delivery"])
        self.assertFalse(result["auto_publish"])

    def test_only_surahs_request_is_a_hard_boundary_for_partial_continuation(self):
        verses = {}
        for surah in (1, 2):
            for ayah in range(1, 4):
                key = f"{surah}:{ayah}"
                verses[key] = {
                    "arabic_uthmani": f"AR {key}",
                    "english_saheeh_international": f"EN {key}",
                    "audio_archive_member": f"{key}.mp3",
                }
        source = {
            "status": "complete_join_candidate_requires_human_review_and_recording_approval",
            "rendering_allowed": False,
            "expected_verse_count": len(verses),
            "verses": verses,
        }
        result = build_review_batch(
            source, count=1, seed="only-surah-two",
            used_ayah_references=["1:1", "1:2"],
            only_surahs=[2],
        )
        self.assertEqual(result["passages"][0]["surah_number"], 2)
        self.assertEqual(result["passages"][0]["verse_numbers"], [1, 2, 3])

if __name__ == "__main__":
    unittest.main()

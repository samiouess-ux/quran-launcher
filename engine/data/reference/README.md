# Quran text reference maintenance

This directory contains reviewed, version-controlled Arabic text snapshots used
by the fail-closed validator. A reference entry is not considered approved merely
because it was copied from a website or passed through the validator.

## Adding verses safely

1. Choose one trusted Quran text source and one script convention. The current
   reference uses **Uthmani** script. Do not mix Uthmani and simplified Arabic
   spellings in the same reference set.
2. Open the exact surah/verse range in the source and verify every character,
   including letters, hamza forms, alif variants, harakat, shadda, sukun,
   maddah, and Quranic annotation marks where present.
3. Preserve the source string exactly. Do not normalize Unicode, strip marks,
   retype from memory, autocorrect, or silently replace characters.
4. Add each verse under its key `SURAH:VERSE` in
   `quran_text_uthmani.json`. Keep the source URL and review metadata accurate.
5. Add the same verse numbers, in the same order, to the content manifest's
   `source.verses` list and its `verses` entries.
6. Have the exact Arabic strings visually reviewed against the selected source
   before setting `review_status` to `reviewed`.
7. Run `python -m unittest discover -s tests -v` and
   `python src/validate_quran_text.py --manifest content/first_video.json`.
8. Review the rendered video manually. Automated equality checks do not prove
   that fonts, shaping, line breaks, or on-screen rendering are visually correct.

## Fail-closed rules

- Missing reference text means rendering must stop.
- Any exact Unicode mismatch means rendering must stop.
- Missing, duplicated, or reordered requested verse entries mean rendering
  must stop.
- Never auto-correct Quran text.
- Do not claim that the local reference snapshot independently verifies its
  source online. The source URL and review status are provenance metadata.

## Current coverage

The current reference snapshot contains Surah Ash-Sharh 94:5-6 and Surah Al-Ikhlas 112:1-4. The exact-text validator checks manifests against these local keys only; it does not independently authenticate the source or verify the text online. Expand the snapshot only when the exact source text has been independently checked and reviewed.

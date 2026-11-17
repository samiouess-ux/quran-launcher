# Quran Launcher — Original Engine Port Status

## Safety boundary
- Destination repository: samiouess-ux/quran-launcher
- Working branch: feature/islamic-tiktok-engine-port
- Source repository: samiouess-ux/IslamicTikTokAutomation
- Source branch: feature/telegram-review-notifications
- Source snapshot commit: a5c65d5330e3cb579629a71d5dedae185ab3efe3
- The source repository and its branch were read only. No changes were made there.
- The quran-launcher main branch was not changed.

## Ported files in this branch
- engine/src/render_video.py — original FFmpeg manifest renderer (1080x1920, 30 fps, max 40 seconds).
- engine/src/render_video_scenes.py — original scene-based renderer with per-ayah overlays, timed scenes, audio synchronization, and background reel.
- engine/src/background_rotation.py — approved background selection/rotation.
- engine/src/hashtag_strategy.py — caption hashtag rotation helper.
- engine/src/validate_content_manifest.py — manifest safety and structure validation.
- engine/src/quran_audio_parts.py — audio helper.
- engine/src/content_rotation.py and engine/src/asset_rotation.py — anti-repeat rotation helpers.
- engine/src/quran_social_caption.py — social caption helper.
- engine/src/build_quran_uthmani_catalog.py and engine/src/build_quran_translation_catalog.py — Quran text/translation catalog builders.
- engine/src/validate_quran_text.py — exact Quran text validation.
- engine/.github/workflows/render-manifest-video.yml — source workflow copy for reference; it is not active because it is nested under engine/.
- engine/data/background_candidates.json — source background video candidate catalog.
- engine/data/background_photos_manifest.json — source photo background catalog.
- engine/data/reference/quran_text_uthmani.json — reviewed Uthmani reference snapshot.
- engine/config/settings.example.json — source settings example.

## Important integration facts
- The current launcher UI still uses its browser Canvas/MediaRecorder renderer. It is not yet connected to the original FFmpeg renderer.
- The copied scene renderer requires a complete validated manifest, processed recitation audio plus per-ayah durations, approved background catalog entries, FFmpeg/ffprobe, Pillow with RAQM, and Amiri Bold fonts.
- The original scene renderer outputs vertical 1080x1920 MP4 at 30 fps and enforces a 40-second maximum.
- The source workflow cannot simply be enabled as copied: it expects the source repository's root-level src/, data/, content/, tests/, and workflow paths. A launcher-specific workflow and manifest-building bridge are still required.
- No live render test has been run in quran-launcher yet.
- No Telegram credentials or secrets were copied.

## Next integration work
1. Complete the required renderer support modules/data and establish a launcher-specific workflow.
2. Build a manifest from the launcher selections (surah, ayah range, reciter, visual/background options) using verified Quran text and paired Saheeh International translation.
3. Connect the UI to the workflow without exposing credentials in browser code.
4. Run a real MP4 render test and verify audio, Arabic/English text, vertical dimensions, timing, and background changes before calling the port complete.
